"""One-time registration of the /audit slash command with Discord.

Run this locally, not in Lambda. The gateway version did this automatically via
`DiliBot.tree.sync()` on startup; with HTTP interactions there is no startup, so
commands are registered explicitly.

Registering to a guild (rather than globally) makes the command appear
instantly instead of taking up to an hour to propagate.

Usage (PowerShell):
    $env:APP_ID="..."; $env:GUILD_ID="..."; $env:BOT_TOKEN="..."
    python register_commands.py
"""

import json
import os
import urllib.error
import urllib.request

APP_ID = os.environ["APP_ID"]
GUILD_ID = os.environ["GUILD_ID"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

COMMANDS = [
    {
        "name": "audit",
        "description": "Audit raid signups against the Raider role",
        "options": [
            {
                "name": "raid_id",
                "description": "The Raid-Helper event ID (found in the event URL)",
                "type": 3,  # STRING
                "required": True,
            }
        ],
    }
]


def main():
    # PUT replaces the full command set for this guild, so removing a command
    # from COMMANDS above also removes it from Discord.
    request = urllib.request.Request(
        f"https://discord.com/api/v10/applications/{APP_ID}/guilds/{GUILD_ID}/commands",
        data=json.dumps(COMMANDS).encode(),
        headers={
            "Authorization": f"Bot {BOT_TOKEN}",
            "Content-Type": "application/json",
            # Discord sits behind Cloudflare, which 403s the default
            # "Python-urllib/x" agent before the request reaches Discord. A real
            # User-Agent is required by the API.
            "User-Agent": "DiliBot (https://github.com/kalesec/DiliBot, 1.0)",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            registered = json.loads(response.read())
    except urllib.error.HTTPError as error:
        # A bare "403 Forbidden" hides whether this is a Cloudflare block or a
        # Discord-level error like "Missing Access" (bot not authorized into the
        # guild with the applications.commands scope). Print the real body.
        print(f"HTTP {error.code} {error.reason}")
        print(error.read().decode(errors="replace"))
        raise

    for command in registered:
        print(f"Registered /{command['name']} (id: {command['id']})")


if __name__ == "__main__":
    main()
