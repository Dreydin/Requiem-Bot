import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

CREATE_CHANNEL_NAME = "Create Group"


@bot.event
async def on_ready():
    print(f"Chameleon online as: {bot.user}")
    print("Watching for players joining Create Group...")


@bot.event
async def on_voice_state_update(member, before, after):

    # Player joins Create Group
    if after.channel is not None and after.channel.name == CREATE_CHANNEL_NAME:

        category = after.channel.category

        channel = await member.guild.create_voice_channel(
            name=f"{member.display_name}'s Group",
            category=category
        )

        await member.move_to(channel)

        print(f"Created group channel for {member.display_name}")

    # Player leaves a temporary group
    if before.channel is not None:

        channel = before.channel

        if (
            channel.name != CREATE_CHANNEL_NAME
            and channel.name.endswith("'s Group")
            and len(channel.members) == 0
        ):
            try:
                await channel.delete()
                print(f"Deleted empty channel: {channel.name}")
            except discord.NotFound:
                pass


token = os.getenv("DISCORD_BOT_TOKEN")

if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN has not been set.")

bot.run(token)
