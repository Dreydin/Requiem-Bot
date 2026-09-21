import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CREATE_CHANNEL_NAME = "➕ Create Group"
TEMP_CHANNELS = set()


@bot.event
async def on_ready():
    print(f"Chameleon online as: {bot.user}")
    print("Watching for players joining Create Group...")
    await bot.tree.sync()


@bot.event
async def on_voice_state_update(member, before, after):
    print(f"VOICE EVENT: {member.display_name} | {before.channel} -> {after.channel}")

    # Player joins Create Group
    if after.channel is not None and after.channel.name == CREATE_CHANNEL_NAME:

        category = after.channel.category

        channel = await member.guild.create_voice_channel(
            name=f"{member.display_name}'s Group",
            category=category
        )

        await member.move_to(channel)
        TEMP_CHANNELS.add(channel.id)

        print(f"Created group channel for {member.display_name}")

    # Player leaves a temporary group
    if before.channel is not None:

        channel = before.channel

        if (
            channel.id in TEMP_CHANNELS
and len(channel.members) == 0
        ):
            try:
                await channel.delete()
                TEMP_CHANNELS.discard(channel.id)
                print(f"Deleted empty channel: {channel.name}")
            except discord.NotFound:
                pass
@bot.tree.command(name="rename", description="Rename your group channel")
async def rename(interaction: discord.Interaction, new_name: str):
    if interaction.user.voice is None:
        await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        return

    channel = interaction.user.voice.channel

    if channel.name == CREATE_CHANNEL_NAME:
        await interaction.response.send_message("You can't rename the Create Group channel.", ephemeral=True)
        return

    await channel.edit(name=new_name)
    await interaction.response.send_message(f"Channel renamed to {new_name}.", ephemeral=True)


token = os.getenv("DISCORD_BOT_TOKEN")

if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN has not been set.")

bot.run(token)
