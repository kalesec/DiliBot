# OS and dotenv are used to load environment variables as to not hardcode token 
import os
from dotenv import load_dotenv
# discord and commands are used to create the bot and handle events and commands
import discord
from discord.ext import commands
# Import to make API call to Raid-Helper
import aiohttp


# Setting permisisons for the Bot
intents = discord.Intents.default()
# Required to read messages. Needed to read the Raid-Helper signups
intents.message_content = True
# Required to read the members of the Raider role
intents.members = True

# Sets prefix for bot usage to ?
DiliBot = commands.Bot(command_prefix="/", intents=intents)

# Confirms the bot is online and prints the bot's username and ID to the console when ran
@DiliBot.event
async def on_ready():  # Single on_ready combining both
    print(f"Logged in as {DiliBot.user} (ID: {DiliBot.user.id})")
    await DiliBot.tree.sync()
    print("Slash commands synced!")

# Defines the /audit command, which takes a raid_id as an argument and audits the raid signups against the Raider role
@DiliBot.tree.command(name="audit", description="Audit raid signups against the Raider role")
@discord.app_commands.describe(raid_id="The Raid-Helper event ID (found in the event URL)")
async def audit(interaction: discord.Interaction, raid_id: str):
    await interaction.response.defer()

    url = f"https://raid-helper.xyz/api/v4/events/{raid_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                await interaction.followup.send(f"Could not fetch raid data. Status: {response.status}. Check the event ID.")
                return
            data = await response.json()

    
    signed_up_ids = set()
    for signup in data.get("signUps", []):
        user_id = signup.get("userId")
        if user_id:
            signed_up_ids.add(str(user_id))

    print(f"Signed up user IDs: {signed_up_ids}")

    guild = interaction.guild
    raider_role = discord.utils.get(guild.roles, name="Raider")

    if not raider_role:
        await interaction.followup.send('Could not find a role named "Raider". Check the role name.')
        return

    not_signed_up = []
    for member in raider_role.members:
        if member.bot:
            continue
        print(f"Checking {member.display_name} (ID: {member.id})")
        if str(member.id) not in signed_up_ids:
            not_signed_up.append(member.display_name)

    if not_signed_up:
        missing = "\n".join(f"- {name}" for name in sorted(not_signed_up))
        await interaction.followup.send(f"**Raiders not signed up ({len(not_signed_up)}):**\n{missing}")
    else:
        await interaction.followup.send("All raiders are signed up!")

# Load environment variables and run the bot
load_dotenv()
token = os.getenv("bot_token")
DiliBot.run(token)