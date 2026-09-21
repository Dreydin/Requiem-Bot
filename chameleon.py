import os
import re
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

CREATE_CHANNEL_NAME = "➕ Create Group"
GROUP_CATEGORY_NAME = "━━ GROUPING ━━"

# Tracks channel ID -> creator ID while the bot is running.
group_owners = {}

# Tracks every temporary channel created during this bot session.
temporary_channels = set()


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as error:
        print(f"COMMAND SYNC ERROR: {repr(error)}")

    print(f"Chameleon online as: {bot.user}")
    print("Watching for players joining Create Group...")
    print("Rename command enabled.")


@bot.event
async def on_voice_state_update(member, before, after):

    # =====================================================
    # CREATE TEMPORARY GROUP
    # =====================================================

    if (
        after.channel is not None
        and after.channel.name == CREATE_CHANNEL_NAME
    ):
        guild = member.guild

        category = discord.utils.get(
            guild.categories,
            name=GROUP_CATEGORY_NAME
        )

        if category is None:
            print("ERROR: GROUPING category could not be found.")
            return

        channel_name = f"{member.display_name}'s Group"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=True,
                connect=True
            )
        }

        try:
            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"CHAMELEON OWNER:{member.id}"
            )

            group_owners[new_channel.id] = member.id
            temporary_channels.add(new_channel.id)

            await member.move_to(new_channel)

            print(
                f"Created temporary group: {channel_name} "
                f"(Owner: {member})"
            )

        except discord.Forbidden:
            print(
                "ERROR: Bot needs permission to create "
                "channels and move members."
            )

        except Exception as error:
            print(f"CREATE ERROR: {repr(error)}")

    # =====================================================
    # DELETE EMPTY TEMPORARY GROUP
    # =====================================================

    if before.channel is not None:

        channel = before.channel

        # Never delete the permanent Create Group channel.
        if channel.name == CREATE_CHANNEL_NAME:
            return

        # Only consider channels inside GROUPING.
        if (
            channel.category is None
            or channel.category.name != GROUP_CATEGORY_NAME
        ):
            return

        # If we created this channel during this session,
        # it remains temporary even after being renamed.
        if channel.id in temporary_channels:

            if len(channel.members) == 0:

                channel_name = channel.name

                temporary_channels.discard(channel.id)
                group_owners.pop(channel.id, None)

                try:
                    await channel.delete(
                        reason="Chameleon temporary group empty"
                    )

                    print(
                        f"Deleted empty temporary group: "
                        f"{channel_name}"
                    )

                except discord.NotFound:
                    pass

                except Exception as error:
                    print(f"DELETE ERROR: {repr(error)}")


# =========================================================
# /RENAME
# =========================================================

@bot.tree.command(
    name="rename",
    description="Rename the temporary voice group you created."
)
@app_commands.describe(
    name="The new name for your voice group"
)
async def rename_group(
    interaction: discord.Interaction,
    name: str
):
    member = interaction.user

    if (
        not isinstance(member, discord.Member)
        or member.voice is None
        or member.voice.channel is None
    ):
        await interaction.response.send_message(
            "You need to be inside your temporary voice group first.",
            ephemeral=True
        )
        return

    channel = member.voice.channel

    if (
        channel.category is None
        or channel.category.name != GROUP_CATEGORY_NAME
        or channel.name == CREATE_CHANNEL_NAME
        or channel.id not in temporary_channels
    ):
        await interaction.response.send_message(
            "This command only works inside a temporary group.",
            ephemeral=True
        )
        return

    owner_id = group_owners.get(channel.id)

    if owner_id != member.id:
        await interaction.response.send_message(
            "Only the person who created this group can rename it.",
            ephemeral=True
        )
        return

    new_name = name.strip()

    # Remove line breaks/control characters.
    new_name = re.sub(r"[\r\n\t]", " ", new_name)

    if not new_name:
        await interaction.response.send_message(
            "Enter a name for the group.",
            ephemeral=True
        )
        return

    if len(new_name) > 100:
        await interaction.response.send_message(
            "That name is too long.",
            ephemeral=True
        )
        return

    try:
        await channel.edit(
            name=new_name,
            reason=f"Temporary group renamed by {member}"
        )

        await interaction.response.send_message(
            f"Group renamed to **{new_name}**.",
            ephemeral=True
        )

        print(
            f"{member} renamed temporary group to: "
            f"{new_name}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "I don't have permission to rename this channel.",
            ephemeral=True
        )

    except Exception as error:
        print(f"RENAME ERROR: {repr(error)}")

        await interaction.response.send_message(
            "Something went wrong while renaming the group.",
            ephemeral=True
        )


TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    print("")
    print("DISCORD_BOT_TOKEN has not been set.")
    print("Set the token before starting Chameleon.")
    print("")
else:
    bot.run(TOKEN)