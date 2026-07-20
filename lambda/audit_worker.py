"""Performs the raid signup audit and edits the deferred Discord response.

Invoked asynchronously by interactions_handler. Because the interaction was
already deferred, this has 15 minutes to work -- far more than it needs.

Ported from the gateway version in DiliBot.py. The audit logic is unchanged;
what differs is how members are obtained: the gateway kept a member cache in
`raider_role.members`, but over REST we page through the guild member list and
filter on each member's role IDs.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

import boto3

APP_ID = os.environ["APP_ID"]
GUILD_ID = os.environ["GUILD_ID"]
TOKEN_PARAM = os.environ["TOKEN_PARAM"]
RAIDER_ROLE_NAME = os.environ.get("RAIDER_ROLE_NAME", "Raider")

DISCORD_API = "https://discord.com/api/v10"
# Discord sits behind Cloudflare, which 403s the default "Python-urllib/x" agent
# before the request reaches Discord. Every call out must carry a real one.
USER_AGENT = "DiliBot (https://github.com/kalesec/DiliBot, 1.0)"
# Discord rejects messages over 2000 characters.
MAX_MESSAGE_LEN = 2000
# Max members Discord returns per page. The request and the "was that the last
# page?" check must agree, so both read this one value.
MEMBER_PAGE_LIMIT = 1000

_ssm = boto3.client("ssm")
_token_cache = None


def _bot_token():
    """Read the bot token from SSM, caching it across warm invocations."""
    global _token_cache
    if _token_cache is None:
        result = _ssm.get_parameter(Name=TOKEN_PARAM, WithDecryption=True)
        _token_cache = result["Parameter"]["Value"]
    return _token_cache


def _get_json(url, headers=None):
    all_headers = {"User-Agent": USER_AGENT}
    if headers:
        all_headers.update(headers)
    request = urllib.request.Request(url, headers=all_headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def _discord_get(path, params=None):
    url = f"{DISCORD_API}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return _get_json(url, {"Authorization": f"Bot {_bot_token()}"})


def _edit_original_response(token, content):
    """Replace the deferred "thinking" state with the real result."""
    if len(content) > MAX_MESSAGE_LEN:
        content = content[: MAX_MESSAGE_LEN - 20].rstrip() + "\n...(truncated)"

    request = urllib.request.Request(
        f"{DISCORD_API}/webhooks/{APP_ID}/{token}/messages/@original",
        data=json.dumps({"content": content}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="PATCH",
    )
    # The interaction token itself authenticates this call -- no bot token.
    with urllib.request.urlopen(request, timeout=15):
        pass


def _fetch_raider_role_id():
    for role in _discord_get(f"/guilds/{GUILD_ID}/roles"):
        if role["name"] == RAIDER_ROLE_NAME:
            return role["id"]
    return None


def _fetch_role_members(role_id):
    """Page through the guild member list, keeping non-bots holding role_id.

    Requires the GUILD_MEMBERS privileged intent, which is enabled on this app.
    """
    members = []
    after = "0"
    while True:
        page = _discord_get(
            f"/guilds/{GUILD_ID}/members",
            {"limit": MEMBER_PAGE_LIMIT, "after": after},
        )
        if not page:
            break
        for member in page:
            user = member["user"]
            if user.get("bot"):
                continue
            if role_id in member.get("roles", []):
                members.append(member)
        after = page[-1]["user"]["id"]
        if len(page) < MEMBER_PAGE_LIMIT:
            break
    return members


def _display_name(member):
    """Match Discord's display precedence: nickname, then global name, then username."""
    user = member["user"]
    return member.get("nick") or user.get("global_name") or user["username"]


def _audit(raid_id):
    """Return the message to show the user. Mirrors DiliBot.py's audit command."""
    try:
        event = _get_json(f"https://raid-helper.xyz/api/v4/events/{raid_id}")
    except urllib.error.HTTPError as error:
        return (
            f"Could not fetch raid data. Status: {error.code}. Check the event ID."
        )
    except urllib.error.URLError:
        return "Could not reach Raid-Helper. Try again in a moment."

    signed_up_ids = {
        str(signup["userId"])
        for signup in event.get("signUps", [])
        if signup.get("userId")
    }

    role_id = _fetch_raider_role_id()
    if role_id is None:
        return (
            f'Could not find a role named "{RAIDER_ROLE_NAME}". Check the role name.'
        )

    not_signed_up = sorted(
        _display_name(member)
        for member in _fetch_role_members(role_id)
        if member["user"]["id"] not in signed_up_ids
    )

    if not not_signed_up:
        return "All raiders are signed up!"

    missing = "\n".join(f"- {name}" for name in not_signed_up)
    return f"**Raiders not signed up ({len(not_signed_up)}):**\n{missing}"


def lambda_handler(event, context):
    token = event["token"]

    # Only answer in the server this bot was deployed for.
    if event.get("guild_id") != GUILD_ID:
        _edit_original_response(token, "This bot is not configured for this server.")
        return

    options = {
        option["name"]: option["value"]
        for option in event.get("data", {}).get("options", [])
    }
    raid_id = options.get("raid_id", "").strip()

    try:
        message = _audit(raid_id)
    except Exception:
        # Never leave the user staring at a permanent "thinking" state.
        # Log the traceback for CloudWatch, but keep the token out of it.
        import traceback

        traceback.print_exc()
        message = "Something went wrong running the audit. Check the logs."

    _edit_original_response(token, message)
