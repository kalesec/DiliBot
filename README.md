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
| Bot goes offline when terminal closes | Deploy to AWS — see [Hosting on AWS](#hosting-on-aws) below |

---

# Hosting on AWS

Running `DiliBot.py` locally keeps a Discord **gateway** (WebSocket) connection open, which is why the bot dies when the terminal closes. Keeping that connection alive 24/7 means paying for an always-on host — about **$7/month** on the cheapest usable EC2 instance.

Because DiliBot only handles slash commands, it does not need that connection. Discord can instead **POST each command to an HTTPS endpoint**, which fits AWS Lambda and lands entirely inside Lambda's permanent free tier.

**Running cost: ~$0.00/month.**

The trade-off: without a gateway connection the bot shows as **offline** in the member list. Slash commands work normally. If DiliBot ever needs to react to events in real time (reminders, message monitoring, welcome messages), it would have to move back to an always-on host.

## Architecture

```
Discord ──POST──► Lambda Function URL ──► dilibot-interactions   (public)
                                           verifies signature, replies within 3s,
                                           hands off — holds no bot token
                                                  │
                                                  ▼ async invoke
                                          dilibot-worker         (private)
                                           reads token from SSM, runs the audit,
                                           edits the reply in place
```

Two functions because Discord requires an initial response within **3 seconds**, which is not enough time for the audit's external API calls. The first function immediately replies "thinking…" (a *deferred* response), which grants a 15-minute window for the worker to fill in the real answer.

Splitting this way also means **the internet-facing function never holds the bot token**.

## Files

| File | Purpose |
|------|---------|
| `lambda/interactions_handler.py` | Public endpoint: signature verification, defer, dispatch |
| `lambda/audit_worker.py` | The audit itself, ported from `DiliBot.py` |
| `lambda/register_commands.py` | One-time `/audit` registration (run locally) |
| `lambda/build.ps1` | Builds both upload zips |
| `lambda/test_*.py` | Offline tests — no AWS or Discord needed |

`DiliBot.py` is kept as the local/gateway version for reference and testing.

## Values you will need

From **Developer Portal → General Information**: `APPLICATION ID` and `PUBLIC KEY`.
From Discord (with Developer Mode on, right-click your server → Copy Server ID): `GUILD_ID`.

## 1. Build

```powershell
.\lambda\build.ps1
```

Produces `lambda/dist/dilibot-interactions.zip` and `lambda/dist/dilibot-worker.zip`.

> PyNaCl contains a compiled extension, so the build pulls the **Linux** wheel rather than the Windows one. No Docker or WSL required.

## 2. Store the bot token

**Systems Manager → Parameter Store → Create parameter**

- Name: `/dilibot/bot_token`
- Type: **SecureString**, KMS key source: **My current account** (`alias/aws/ssm`)
- Value: your bot token

Standard-tier parameters are free.

## 3. Create two IAM roles

**Roles → Create role → AWS service → Lambda**, attaching `AWSLambdaBasicExecutionRole` to each.

**`dilibot-worker-role`** — add this inline policy (substitute your region and account ID):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "ssm:GetParameter",
    "Resource": "arn:aws:ssm:<REGION>:<ACCOUNT_ID>:parameter/dilibot/bot_token"
  }]
}
```

> No `kms:Decrypt` statement is needed here: the AWS-managed `aws/ssm` key already permits decryption by account principals when the call goes through SSM. You would only add one if you switched to a customer-managed key.

**`dilibot-interactions-role`** — add this inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "lambda:InvokeFunction",
    "Resource": "arn:aws:lambda:<REGION>:<ACCOUNT_ID>:function:dilibot-worker"
  }]
}
```

## 4. Create the worker function

### Create it

**Lambda → Create function → Author from scratch.** The create screen only sets the basics — the zip, handler, and config come after.

- **Function name:** `dilibot-worker`
- **Runtime:** Python 3.13
- **Architecture:** x86_64
- **Change default execution role → Use an existing role →** `dilibot-worker-role`

Click **Create function**.

### Then configure it

On the function's detail page, each item below is a separate **Save**:

- **Code** tab → **Upload from → .zip file** → `dilibot-worker.zip`
- **Code** tab → **Runtime settings → Edit** → **Handler:** `audit_worker.lambda_handler`
- **Configuration → General configuration → Edit** → memory 256 MB, timeout 60s
- **Configuration → Environment variables → Edit:**

  | Key | Value |
  |-----|-------|
  | `APP_ID` | your application ID |
  | `GUILD_ID` | your server ID |
  | `TOKEN_PARAM` | `/dilibot/bot_token` |
  | `RAIDER_ROLE_NAME` | `Raider` *(optional)* |

## 5. Create the interactions function

### Create it

Same flow as step 4 — **Lambda → Create function → Author from scratch.**

- **Function name:** `dilibot-interactions`
- **Runtime:** Python 3.13
- **Architecture:** x86_64
- **Change default execution role → Use an existing role →** `dilibot-interactions-role`

Click **Create function**.

### Then configure it

On the function's detail page, each item is a separate **Save**:

- **Code** tab → **Upload from → .zip file** → `dilibot-interactions.zip`
- **Code** tab → **Runtime settings → Edit** → **Handler:** `interactions_handler.lambda_handler`
- **Configuration → General configuration → Edit** → memory 128 MB, timeout 10s
- **Configuration → Environment variables → Edit:**

  | Key | Value |
  |-----|-------|
  | `DISCORD_PUBLIC_KEY` | your application public key |
  | `WORKER_FUNCTION_NAME` | `dilibot-worker` |

- **Configuration → Function URL → Create**, auth type **NONE**. Copy the URL.
  Discord cannot sign AWS SigV4 requests, so the endpoint must be open — the Ed25519 signature check in the handler is what actually authenticates callers.
- **Configuration → Concurrency → Reserve concurrency: 5.**
  Function URLs have no built-in throttling. This caps both damage and cost if the URL is ever discovered and hammered.

## 6. Set log retention and a budget

For **both** `/aws/lambda/dilibot-*` log groups in CloudWatch, set **Retention: 2 weeks**. The default is *Never expire*, which is the one way this setup slowly starts costing money.

Then **Billing → Budgets** → a $5/month cost budget as a backstop alarm.

## 7. Point Discord at the endpoint

**Developer Portal → General Information → Interactions Endpoint URL** → paste the Function URL → **Save**.

Discord immediately sends a signed PING and refuses to save unless it receives a valid response — so a successful save proves the whole chain works.

## 8. Register the slash command

Registration used to happen automatically via `tree.sync()` on startup. With no startup, it is explicit and one-time:

```powershell
$env:APP_ID="..."; $env:GUILD_ID="..."; $env:BOT_TOKEN="..."
python lambda\register_commands.py
```

Guild-scoped commands appear instantly; global ones can take up to an hour.

## 9. Cut over

1. Run `/audit <raid_id>` in Discord and confirm it works.
2. **Regenerate the bot token** in the Developer Portal and update `/dilibot/bot_token`. This kills the copy sitting in plaintext in your local `.env`.
3. Stop the local `python DiliBot.py` process.

## Running the tests

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pynacl boto3
cd lambda
..\.venv\Scripts\python.exe test_interactions_handler.py
..\.venv\Scripts\python.exe test_audit_worker.py
```

These run fully offline. The signature tests matter most — that check is the only thing between the public internet and the worker.

## AWS troubleshooting

| Issue | Fix |
|-------|-----|
| Portal rejects the Interactions Endpoint URL | `DISCORD_PUBLIC_KEY` is wrong, or the function was not deployed before saving. Check the `dilibot-interactions` logs. |
| `Unable to import module 'interactions_handler'` | The zip was built with `Compress-Archive` instead of `build.ps1`, producing Windows-style paths. Rebuild. |
| Command stays stuck on "thinking…" | The worker failed. Check `/aws/lambda/dilibot-worker` logs — usually a missing env var or the SSM policy. |
| "This bot is not configured for this server." | `GUILD_ID` on the worker does not match the server the command ran in. |
| `AccessDeniedException` on `ssm:GetParameter` | The parameter ARN in the worker policy does not match the actual parameter. |
| `register_commands.py` fails with `HTTP Error 403: Forbidden` | The script prints Discord's response body. `Missing Access` (code 50001) means the app was invited without the `applications.commands` scope — re-run the OAuth2 URL with both scopes ticked. A Cloudflare block page means the `User-Agent` header is missing (already set in the script). |
