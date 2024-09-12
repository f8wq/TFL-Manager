import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from flask import Flask
from threading import Thread

# Define intents to allow the bot to receive certain events
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True  # Enable reaction tracking
intents.guilds = True
intents.members = True  # Added to access member roles

# Create a bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Get your bot token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Define your role name here
APPROVER_ROLE_NAME = "record perms"

# Define your channel IDs here
approval_channel_id = 1283584573862842398  # Channel where submissions go for approval
final_channel_id = 1283584751566983301     # Channel where approved submissions are posted

# Global dictionary to keep track of submissions
submissions = {}

# Function to run when bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        # Sync the commands
        await bot.tree.sync()
        print('Commands synced.')
    except Exception as e:
        print(f'Error syncing commands: {e}')

# Define the /record command
@bot.tree.command(name="record", description="Manage level completion records")
async def record(interaction: discord.Interaction):
    await interaction.response.send_message("Use /record_submit to submit a record.\n\n", ephemeral=True)

# Define the /record_submit command
@bot.tree.command(name="record_submit", description="Submit a level completion record")
@app_commands.describe(level="Enter the level name", completion="Describe the completion details", framerate="Enter the framerate", username="Enter the username")
async def record_submit(interaction: discord.Interaction, level: str, completion: str, framerate: str, username: str):
    # Validate input
    if not level or not completion or not framerate or not username:
        await interaction.response.send_message("All fields are required: level, completion, framerate, and username.", ephemeral=True)
        return

    # Fetch the approval channel
    approval_channel = bot.get_channel(approval_channel_id)

    if approval_channel:
        # Send the submission to the approval channel
        approval_message = await approval_channel.send(
            f"**New Submission for Approval**\n**Level:** {level}\n**Completion:** {completion}\n**Framerate:** {framerate}\n**Username:** {username}\n\nReact with ✅ to approve or ❌ to reject."
        )

        # Store the message ID and user ID
        submissions[approval_message.id] = {
            "submitter_id": interaction.user.id,
            "level": level,
            "completion": completion,
            "framerate": framerate,
            "username": username
        }

        # React with ✅ and ❌ to allow the approvers to approve or reject it
        await approval_message.add_reaction('✅')
        await approval_message.add_reaction('❌')

        # Let the user know their submission is under review with the level name
        await interaction.response.send_message(f"Your record for **{level}** has been submitted for approval.", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find the approval channel.", ephemeral=True)

# Event listener for reactions (approval and rejection)
@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    if reaction.message.channel.id == approval_channel_id:
        # Check if the reaction is the ✅ emoji for approval
        if str(reaction.emoji) == '✅':
            guild = reaction.message.guild
            member = guild.get_member(user.id)

            approver_role = discord.utils.get(guild.roles, name=APPROVER_ROLE_NAME)
            if approver_role in member.roles:
                final_channel = bot.get_channel(final_channel_id)
                if final_channel:
                    # Remove the "React with ✅ to approve or ❌ to reject." part from the message
                    content_to_send = reaction.message.content
                    content_to_send = content_to_send.replace(
                        "React with ✅ to approve or ❌ to reject.",
                        ""
                    ).strip()  # Remove any extra new lines

                    # Send the approved message to the final channel
                    await final_channel.send(f"**Approved Submission**\n{content_to_send}")
                    await reaction.message.reply(f"Submission approved by {user.display_name}!")

                    # Optionally remove the submission record
                    submissions.pop(reaction.message.id, None)
                else:
                    await reaction.message.reply("...")

        # Check if the reaction is the ❌ emoji for rejection
        elif str(reaction.emoji) == '❌':
            guild = reaction.message.guild
            member = guild.get_member(user.id)

            approver_role = discord.utils.get(guild.roles, name=APPROVER_ROLE_NAME)
            if approver_role in member.roles:
                await reaction.message.delete()  # Deletes the message if rejected
                await reaction.message.channel.send(f"Submission rejected by {user.display_name}.")

                # Notify the submitter
                submitter_id = submissions.get(reaction.message.id, {}).get('submitter_id')
                if submitter_id:
                    submitter = guild.get_member(submitter_id)
                    if submitter:
                        await submitter.send(f"Your record submission for **{submissions.get(reaction.message.id, {}).get('level', 'unknown level')}** was rejected by {user.display_name}.")

                # Optionally remove the submission record
                submissions.pop(reaction.message.id, None)

# Function to keep the bot alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Call keep_alive before running the bot
keep_alive()
bot.run(TOKEN)
