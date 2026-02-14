# bot.py

import discord
from discord import app_commands
from discord.ext import tasks
import json
import os
import asyncio
from datetime import datetime

# ============ CONFIGURATION ============
BOT_TOKEN = "MTMwMTE1MTU5MjcwNzUyNjY5OA.GhcFNU.oxT76xXnBkehGtUx_JBMb8esAesgykTSwKN-LU"
DATA_FILE = "voice_channels.json"
# =======================================


class VoiceBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.active_channels = {}  # guild_id: channel_id
        self.load_data()

    def load_data(self):
        """Load saved voice channel data from file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    self.active_channels = {int(k): int(v) for k, v in data.items()}
                    print(f"📂 Loaded {len(self.active_channels)} saved voice channel(s).")
            except Exception as e:
                print(f"⚠️ Error loading data: {e}")
                self.active_channels = {}
        else:
            self.active_channels = {}

    def save_data(self):
        """Save active voice channel data to file."""
        try:
            with open(DATA_FILE, "w") as f:
                json.dump({str(k): v for k, v in self.active_channels.items()}, f, indent=4)
        except Exception as e:
            print(f"⚠️ Error saving data: {e}")

    async def setup_hook(self):
        """Called when the bot is ready to set up commands."""
        await self.tree.sync()
        print("🔄 Slash commands synced!")
        self.reconnect_task.start()
        self.keep_alive_task.start()

    @tasks.loop(seconds=30)
    async def keep_alive_task(self):
        """Periodically check if the bot is still connected to saved channels."""
        for guild_id, channel_id in list(self.active_channels.items()):
            guild = self.get_guild(guild_id)
            if guild is None:
                continue

            voice_client = guild.voice_client

            # If not connected or connected to wrong channel, reconnect
            if voice_client is None or not voice_client.is_connected():
                channel = guild.get_channel(channel_id)
                if channel is None:
                    continue
                try:
                    await channel.connect(reconnect=True, self_deaf=True)
                    print(f"🔁 Reconnected to #{channel.name} in {guild.name}")
                except Exception as e:
                    print(f"⚠️ Failed to reconnect in {guild.name}: {e}")
            elif voice_client.channel.id != channel_id:
                channel = guild.get_channel(channel_id)
                if channel is None:
                    continue
                try:
                    await voice_client.move_to(channel)
                    print(f"🔁 Moved to correct channel #{channel.name} in {guild.name}")
                except Exception as e:
                    print(f"⚠️ Failed to move in {guild.name}: {e}")

    @keep_alive_task.before_loop
    async def before_keep_alive(self):
        await self.wait_until_ready()

    @tasks.loop(count=1)
    async def reconnect_task(self):
        """Reconnect to all saved voice channels on startup."""
        await self.wait_until_ready()
        await asyncio.sleep(3)  # Small delay to ensure everything is ready

        print("🔌 Reconnecting to saved voice channels...")
        for guild_id, channel_id in list(self.active_channels.items()):
            guild = self.get_guild(guild_id)
            if guild is None:
                print(f"⚠️ Guild {guild_id} not found. Removing from saved data.")
                del self.active_channels[guild_id]
                self.save_data()
                continue

            channel = guild.get_channel(channel_id)
            if channel is None:
                print(f"⚠️ Channel {channel_id} not found in {guild.name}. Removing.")
                del self.active_channels[guild_id]
                self.save_data()
                continue

            try:
                if guild.voice_client is not None:
                    await guild.voice_client.disconnect(force=True)
                await channel.connect(reconnect=True, self_deaf=True)
                print(f"✅ Reconnected to #{channel.name} in {guild.name}")
            except Exception as e:
                print(f"⚠️ Failed to reconnect to #{channel.name} in {guild.name}: {e}")

        print("🔌 Reconnection process complete!")


# Create bot instance
bot = VoiceBot()


# ============ HELPER FUNCTIONS ============

def create_embed(title: str, description: str, color: discord.Color, channel_name: str = None, footer: str = None):
    """Create a styled embed message."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    if channel_name:
        embed.add_field(name="🔊 Voice Channel", value=f"`{channel_name}`", inline=True)
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text="24/7 Voice Bot")
    return embed


# ============ SLASH COMMANDS ============

@bot.tree.command(name="247", description="Make the bot join a voice channel and stay 24/7")
@app_commands.describe(channel="The voice channel to join (mention or paste ID)")
@app_commands.checks.has_permissions(manage_channels=True)
async def join_247(interaction: discord.Interaction, channel: str):
    """Join a voice channel and stay connected 24/7."""

    await interaction.response.defer(ephemeral=False)

    guild = interaction.guild

    if guild is None:
        embed = create_embed(
            title="❌ Error",
            description="This command can only be used in a server!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    # Parse channel from mention or ID
    voice_channel = None

    # Try to extract channel ID from mention format <#123456789>
    channel_str = channel.strip()
    if channel_str.startswith("<#") and channel_str.endswith(">"):
        channel_id_str = channel_str[2:-1]
        try:
            channel_id = int(channel_id_str)
            voice_channel = guild.get_channel(channel_id)
        except ValueError:
            pass
    else:
        # Try as raw ID
        try:
            channel_id = int(channel_str)
            voice_channel = guild.get_channel(channel_id)
        except ValueError:
            # Try to find by name
            voice_channel = discord.utils.get(guild.voice_channels, name=channel_str)

    # Validate channel
    if voice_channel is None:
        embed = create_embed(
            title="❌ Channel Not Found",
            description=f"Could not find a channel matching `{channel}`.\n\n**Usage:**\n• Mention: `/247 channel:#voice-chat`\n• ID: `/247 channel:123456789012345678`\n• Name: `/247 channel:General`",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    if not isinstance(voice_channel, (discord.VoiceChannel, discord.StageChannel)):
        embed = create_embed(
            title="❌ Invalid Channel",
            description=f"<#{voice_channel.id}> is not a voice channel! Please provide a valid voice channel.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    # Check bot permissions
    permissions = voice_channel.permissions_for(guild.me)
    if not permissions.connect or not permissions.speak:
        embed = create_embed(
            title="❌ Missing Permissions",
            description=f"I don't have permission to **connect** or **speak** in <#{voice_channel.id}>.\nPlease grant me the required permissions.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    # Check if already connected to this channel
    if guild.id in bot.active_channels and bot.active_channels[guild.id] == voice_channel.id:
        if guild.voice_client and guild.voice_client.is_connected():
            embed = create_embed(
                title="ℹ️ Already Connected",
                description=f"I'm already connected to <#{voice_channel.id}> in 24/7 mode!",
                color=discord.Color.blue(),
                channel_name=voice_channel.name
            )
            await interaction.followup.send(embed=embed)
            return

    # Disconnect from existing connection if any
    if guild.voice_client is not None:
        try:
            await guild.voice_client.disconnect(force=True)
        except Exception:
            pass

    # Connect to the voice channel
    try:
        await voice_channel.connect(reconnect=True, self_deaf=True)

        # Save to active channels
        bot.active_channels[guild.id] = voice_channel.id
        bot.save_data()

        embed = create_embed(
            title="✅ 24/7 Mode Activated",
            description=f"I've joined <#{voice_channel.id}> and will stay connected **24/7**!\n\nUse `/leave247` to disconnect me.",
            color=discord.Color.green(),
            channel_name=voice_channel.name,
            footer=f"Requested by {interaction.user.display_name}"
        )
        embed.add_field(name="📌 Status", value="`🟢 Connected`", inline=True)
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        await interaction.followup.send(embed=embed)
        print(f"✅ Joined #{voice_channel.name} in {guild.name} (24/7 mode)")

    except discord.errors.ClientException as e:
        embed = create_embed(
            title="❌ Connection Error",
            description=f"Failed to connect: `{str(e)}`",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)

    except Exception as e:
        embed = create_embed(
            title="❌ Unexpected Error",
            description=f"An unexpected error occurred: `{str(e)}`",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)


@bot.tree.command(name="leave247", description="Make the bot leave the 24/7 voice channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def leave_247(interaction: discord.Interaction):
    """Leave the 24/7 voice channel."""

    await interaction.response.defer(ephemeral=False)

    guild = interaction.guild

    if guild is None:
        embed = create_embed(
            title="❌ Error",
            description="This command can only be used in a server!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    # Check if bot is in 24/7 mode in this guild
    if guild.id not in bot.active_channels:
        embed = create_embed(
            title="❌ Not Active",
            description="I'm not in 24/7 mode in this server!\nUse `/247` to activate it first.",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)
        return

    # Get the channel name before disconnecting
    channel_id = bot.active_channels[guild.id]
    channel = guild.get_channel(channel_id)
    channel_name = channel.name if channel else "Unknown"

    # Disconnect
    try:
        if guild.voice_client is not None:
            await guild.voice_client.disconnect(force=True)
    except Exception:
        pass

    # Remove from active channels
    del bot.active_channels[guild.id]
    bot.save_data()

    embed = create_embed(
        title="👋 24/7 Mode Deactivated",
        description=f"I've left the voice channel and disabled 24/7 mode.\n\nUse `/247` to activate it again.",
        color=discord.Color.red(),
        channel_name=channel_name,
        footer=f"Requested by {interaction.user.display_name}"
    )
    embed.add_field(name="📌 Status", value="`🔴 Disconnected`", inline=True)
    embed.set_thumbnail(url=bot.user.display_avatar.url)

    await interaction.followup.send(embed=embed)
    print(f"👋 Left #{channel_name} in {guild.name} (24/7 mode disabled)")


@bot.tree.command(name="status247", description="Check the current 24/7 voice channel status")
async def status_247(interaction: discord.Interaction):
    """Check the bot's 24/7 status in this server."""

    guild = interaction.guild

    if guild is None:
        embed = create_embed(
            title="❌ Error",
            description="This command can only be used in a server!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    if guild.id in bot.active_channels:
        channel_id = bot.active_channels[guild.id]
        channel = guild.get_channel(channel_id)
        is_connected = guild.voice_client is not None and guild.voice_client.is_connected()

        if channel:
            status_text = "🟢 Connected" if is_connected else "🟡 Reconnecting..."
            color = discord.Color.green() if is_connected else discord.Color.yellow()

            embed = create_embed(
                title="📊 24/7 Status",
                description=f"24/7 mode is **active** in this server.",
                color=color,
                channel_name=channel.name
            )
            embed.add_field(name="📌 Status", value=f"`{status_text}`", inline=True)
            embed.add_field(name="🆔 Channel ID", value=f"`{channel_id}`", inline=True)
            embed.set_thumbnail(url=bot.user.display_avatar.url)
        else:
            embed = create_embed(
                title="📊 24/7 Status",
                description="24/7 mode is **active** but the saved channel was not found.\nUse `/leave247` and set it up again.",
                color=discord.Color.orange()
            )
    else:
        embed = create_embed(
            title="📊 24/7 Status",
            description="24/7 mode is **not active** in this server.\nUse `/247` to activate it!",
            color=discord.Color.greyple()
        )

    await interaction.response.send_message(embed=embed)


# ============ ERROR HANDLERS ============

@join_247.error
async def join_247_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        embed = create_embed(
            title="🔒 Permission Denied",
            description="You need the **Manage Channels** permission to use this command!",
            color=discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = create_embed(
            title="❌ Error",
            description=f"An error occurred: `{str(error)}`",
            color=discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


@leave_247.error
async def leave_247_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        embed = create_embed(
            title="🔒 Permission Denied",
            description="You need the **Manage Channels** permission to use this command!",
            color=discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = create_embed(
            title="❌ Error",
            description=f"An error occurred: `{str(error)}`",
            color=discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


# ============ EVENTS ============

@bot.event
async def on_ready():
    print(f"{'='*50}")
    print(f"🤖 Bot is ready!")
    print(f"📛 Logged in as: {bot.user.name}#{bot.user.discriminator}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"🌐 Connected to {len(bot.guilds)} guild(s)")
    print(f"📂 Active 24/7 channels: {len(bot.active_channels)}")
    print(f"{'='*50}")

    # Set bot activity
    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="24/7 Voice 🎵"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Handle when the bot gets disconnected by someone."""
    if member.id != bot.user.id:
        return

    guild = member.guild

    # Bot was disconnected from a voice channel
    if before.channel is not None and after.channel is None:
        if guild.id in bot.active_channels:
            # Wait a moment then try to reconnect
            await asyncio.sleep(2)

            channel_id = bot.active_channels.get(guild.id)
            if channel_id is None:
                return

            channel = guild.get_channel(channel_id)
            if channel is None:
                return

            try:
                if guild.voice_client is not None:
                    try:
                        await guild.voice_client.disconnect(force=True)
                    except Exception:
                        pass

                await channel.connect(reconnect=True, self_deaf=True)
                print(f"🔁 Auto-reconnected to #{channel.name} in {guild.name} after disconnect")
            except Exception as e:
                print(f"⚠️ Failed to auto-reconnect in {guild.name}: {e}")
                # Try again after a longer delay
                await asyncio.sleep(5)
                try:
                    if guild.voice_client is not None:
                        try:
                            await guild.voice_client.disconnect(force=True)
                        except Exception:
                            pass
                    await channel.connect(reconnect=True, self_deaf=True)
                    print(f"🔁 Auto-reconnected (retry) to #{channel.name} in {guild.name}")
                except Exception as e2:
                    print(f"⚠️ Failed to auto-reconnect (retry) in {guild.name}: {e2}")

    # Bot was moved to a different channel
    elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        if guild.id in bot.active_channels:
            target_channel_id = bot.active_channels[guild.id]
            if after.channel.id != target_channel_id:
                # Bot was moved to wrong channel, move back
                await asyncio.sleep(1)
                target_channel = guild.get_channel(target_channel_id)
                if target_channel:
                    try:
                        await guild.voice_client.move_to(target_channel)
                        print(f"🔁 Moved back to #{target_channel.name} in {guild.name}")
                    except Exception as e:
                        print(f"⚠️ Failed to move back in {guild.name}: {e}")


# ============ RUN THE BOT ============

if __name__ == "__main__":
    print("🚀 Starting 24/7 Voice Bot...")
    bot.run(BOT_TOKEN)