"""Offline tests for the audit logic ported from the gateway version.

The risky part of the port is member fetching: the gateway kept a cached
`raider_role.members` list, while this version pages the REST API and filters on
role IDs. These tests exercise that loop and the display-name precedence without
touching Discord, Raid-Helper, or AWS.

Usage:  python test_audit_worker.py
"""

import json
import os
import sys
import urllib.error
import urllib.parse
from unittest import mock

os.environ["APP_ID"] = "app-1"
os.environ["GUILD_ID"] = "guild-1"
os.environ["TOKEN_PARAM"] = "/dilibot/bot_token"

_fake_ssm = mock.MagicMock()
_fake_ssm.get_parameter.return_value = {"Parameter": {"Value": "fake-token"}}
with mock.patch("boto3.client", return_value=_fake_ssm):
    import audit_worker


def _member(user_id, username, roles, nick=None, global_name=None, bot=False):
    return {
        "nick": nick,
        "roles": roles,
        "user": {
            "id": user_id,
            "username": username,
            "global_name": global_name,
            "bot": bot,
        },
    }


# A guild spanning two pages, to force the `after` cursor loop to run twice.
PAGE_SIZE = 3
ROLES = [{"id": "role-raider", "name": "Raider"}, {"id": "role-other", "name": "Guest"}]
MEMBERS = [
    _member("1", "alice", ["role-raider"], nick="Alice the Bold"),
    _member("2", "bob", ["role-raider"], global_name="Bobby"),
    _member("3", "carol", ["role-raider"]),
    _member("4", "dave", ["role-other"]),  # not a Raider
    _member("5", "raidbot", ["role-raider"], bot=True),  # bot, must be skipped
    _member("6", "erin", ["role-raider", "role-other"]),
]
SIGNED_UP = ["1", "3"]


def _fake_get_json(url, headers=None):
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    if "raid-helper.xyz" in url:
        return {"signUps": [{"userId": uid} for uid in SIGNED_UP]}
    if parsed.path.endswith("/roles"):
        return ROLES
    if parsed.path.endswith("/members"):
        after = params["after"][0]
        start = next(
            (i + 1 for i, m in enumerate(MEMBERS) if m["user"]["id"] == after), 0
        )
        return MEMBERS[start : start + PAGE_SIZE]
    raise AssertionError(f"unexpected URL: {url}")


def _check(name, condition, detail=""):
    print(f"{'PASS' if condition else 'FAIL'}  {name}{detail}")
    return condition


def main():
    results = []

    # Shrink the page size so this small fixture spans multiple pages and the
    # `after` cursor loop actually runs. Only _get_json is stubbed, so the real
    # URL building and pagination logic are under test.
    with mock.patch.object(audit_worker, "_get_json", side_effect=_fake_get_json), \
         mock.patch.object(audit_worker, "MEMBER_PAGE_LIMIT", PAGE_SIZE):
        message = audit_worker._audit("1514020131834036406")

    # Expected: alice(1) and carol(3) signed up. dave lacks the role, raidbot is
    # a bot. So bob and erin are missing, sorted by display name.
    results.append(
        _check(
            "reports only unsigned non-bot Raiders, across pages",
            message == "**Raiders not signed up (2):**\n- Bobby\n- erin",
            f"\n      got: {message!r}",
        )
    )
    results.append(
        _check("uses global_name when no nickname is set", "Bobby" in message)
    )
    results.append(_check("excludes bots holding the Raider role", "raidbot" not in message))
    results.append(_check("excludes members without the Raider role", "dave" not in message))
    results.append(
        _check("excludes signed-up members", "Alice" not in message and "carol" not in message)
    )

    # Everyone signed up.
    with mock.patch.object(audit_worker, "_get_json") as get_json, \
         mock.patch.object(audit_worker, "_discord_get") as discord_get:
        get_json.return_value = {
            "signUps": [{"userId": m["user"]["id"]} for m in MEMBERS]
        }
        discord_get.side_effect = lambda path, params=None: (
            ROLES if path.endswith("/roles") else []
        )
        message = audit_worker._audit("x")
    results.append(_check("all signed up reports success", message == "All raiders are signed up!"))

    # Missing role.
    with mock.patch.object(audit_worker, "_get_json") as get_json, \
         mock.patch.object(audit_worker, "_discord_get") as discord_get:
        get_json.return_value = {"signUps": []}
        discord_get.side_effect = lambda path, params=None: (
            [{"id": "r", "name": "Guest"}] if path.endswith("/roles") else []
        )
        message = audit_worker._audit("x")
    results.append(
        _check("missing Raider role reports a clear error", "Could not find a role" in message)
    )

    # Bad raid ID -- Raid-Helper returns 404.
    with mock.patch.object(
        audit_worker,
        "_get_json",
        side_effect=urllib.error.HTTPError("u", 404, "Not Found", {}, None),
    ):
        message = audit_worker._audit("nope")
    results.append(
        _check("bad raid ID surfaces a status message", "Status: 404" in message)
    )

    # Over-long output must be truncated to Discord's 2000 character limit.
    with mock.patch("urllib.request.urlopen") as urlopen:
        audit_worker._edit_original_response("tok", "x" * 5000)
        sent = json.loads(urlopen.call_args[0][0].data)
    results.append(
        _check(
            "long member lists are truncated below Discord's 2000 char limit",
            len(sent["content"]) <= 2000 and sent["content"].endswith("(truncated)"),
        )
    )

    print()
    if all(results):
        print(f"All {len(results)} checks passed.")
        return 0
    print(f"{results.count(False)} of {len(results)} checks FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
