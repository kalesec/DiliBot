# DiliBot
## Raid-Helper Signup Auditor

DiliBot is a Discord bot that audits raid signups by comparing members with the **Raider** role against signups on a Raid-Helper event. It quickly identifies who has not signed up for a raid.

---

## Requirements

- Python 3.8+
- A Discord account with access to the [Discord Developer Portal](https://discord.com/developers/applications)
- A Raid-Helper bot already set up in your server

---

## Installation

**1. Clone or download the bot files**

**2. Install dependencies**
```bash
pip install discord.py python-dotenv aiohttp
```

**3. Create a `.env` file** in the same folder as `DiliBot.py`:
```
bot_token=your_discord_bot_token_here
```

---
# Create Your Own Bot

### Discord Developer Portal Setup 
1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Go to the **Bot** tab and click **Add Bot**
4. Copy your **Bot Token** and paste it into your `.env` file
5. Under **Privileged Gateway Intents**, enable all three:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
6. Click **Save Changes**

---

## Adding the Bot to Your Server

1. In the Developer Portal go to **OAuth2 → URL Generator**
2. Under **Scopes** select:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Under **Bot Permissions** select:
   - ✅ View Channels
   - ✅ Send Messages
   - ✅ Read Message History
4. Copy the generated URL, open it in a browser, and select your server

---

# Running the Bot

```bash
python DiliBot.py
```

You should see the following in your terminal when it starts successfully:
```
Logged in as DiliBot#1234 (ID: 123456789)
Slash commands synced!
```

---

## Usage

### `/audit <raid_id>`

Audits a Raid-Helper event against all members with the **Raider** role.

| Parameter | Description |
|-----------|-------------|
| `raid_id` | The Raid-Helper event ID |

**Finding the Raid ID:**

The event ID is found in the Raid-Helper message — click **Web View** and copy the number at the end of the URL:
```
https://raid-helper.xyz/event/1514020131834036406
                                ^^^^^^^^^^^^^^^^^^
                                This is the raid_id
```

**Example usage in Discord:**
```
/audit 1514020131834036406
```

**Example output:**
```
Raiders not signed up (3):
- GoofBallEpicMoment
- NerdAlert22
- ExamplePlayerName
```

---

## How It Works

1. You run `/audit <raid_id>` in Discord
2. DiliBot fetches the event data from the Raid-Helper API
3. DiliBot fetches all members in your server with the **Raider** role
4. It compares the two lists by Discord user ID
5. Anyone with the Raider role who is not signed up is listed in the output

Bots are automatically excluded from the audit.

Anyone who has signed up in any capacity (including Bench, Tentative, Late, or Absence) is counted as signed up.

---

## Restricting Access

By default anyone in the server can run `/audit`. To restrict it:

**Option 1 — Role restriction in code**

Add this to the top of the `audit` function in `DiliBot.py` and replace the desired user role within the `name` variable":
```python
allowed_role = discord.utils.get(interaction.guild.roles, name="<REPLACE_ROLE_HERE>")
if allowed_role not in interaction.user.roles:
    await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
    return
```

**Option 2 — Discord's built-in permissions (no code needed)**

Go to **Server Settings → Integrations → DiliBot** and restrict which roles or channels can use the command.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `session has been invalidated` | Regenerate your token in the Developer Portal and update `.env` |
| `Token loaded: None` | Check your `.env` file is in the same folder as `DiliBot.py` and has no quotes around the token |
| Bot doesn't respond to `/audit` | Wait 1-2 minutes after startup for slash commands to sync, then try again |
| `Could not find a role named "Raider"` | The role name is case-sensitive — check it matches exactly in your server |
| All raiders show as signed up | Make sure **Server Members Intent** is enabled in the Developer Portal |
| Bot goes offline when terminal closes | Host the bot on a server or service like Railway or a VPS |
