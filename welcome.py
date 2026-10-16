"""Powitanie nowych członków — embed z avatarem na konfigurowalnym kanale."""
import os
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from . import storage


def _resolve_welcome_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    # 1) Nadpisanie per-guild (ustawione komendą)
    cfg = storage.get_guild_config(guild.id)
    chan_id = cfg.get("welcome_channel_id")
    if chan_id:
        ch = guild.get_channel(int(chan_id))
        if isinstance(ch, discord.TextChannel):
            return ch
    # 2) Fallback do zmiennej środowiskowej
    env_id = os.environ.get("WELCOME_CHANNEL_ID")
    if env_id:
        ch = guild.get_channel(int(env_id))
        if isinstance(ch, discord.TextChannel):
            return ch
    return None


def _build_welcome_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎉 Witaj na serwerze {member.guild.name}!",
        description=(
            f"Cześć {member.mention}! Miło Cię tu widzieć 👋\n\n"
            f"Jesteś naszym **{member.guild.member_count}.** członkiem.\n"
            f"Zapoznaj się z regulaminem i śmiało otwieraj ticket, jeśli masz pytania."
        ),
        color=discord.Color.from_rgb(88, 101, 242),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    footer_icon = member.guild.icon.url if member.guild.icon else None
    embed.set_footer(
        text=f"Konto utworzone • {member.created_at.strftime('%d.%m.%Y')}",
        icon_url=footer_icon,
    )
    return embed


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        channel = _resolve_welcome_channel(member.guild)
        if not channel:
            return
        try:
            await channel.send(embed=_build_welcome_embed(member))
        except discord.Forbidden:
            pass

    @app_commands.command(
        name="set-welcome-channel",
        description="Ustawia kanał, na którym bot będzie witał nowych członków.",
    )
    @app_commands.describe(channel="Kanał powitań.")
    @app_commands.default_permissions(manage_guild=True)
    async def set_welcome_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        storage.set_guild_value(interaction.guild.id, "welcome_channel_id", channel.id)
        await interaction.response.send_message(
            f"✅ Kanał powitań ustawiony na {channel.mention}.", ephemeral=True
        )

    @app_commands.command(
        name="test-welcome",
        description="Wysyła testowe powitanie dla Ciebie na skonfigurowany kanał.",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def test_welcome(self, interaction: discord.Interaction):
        channel = _resolve_welcome_channel(interaction.guild)
        if not channel:
            await interaction.response.send_message(
                "❌ Brak skonfigurowanego kanału. Użyj `/set-welcome-channel`.", ephemeral=True
            )
            return
        await channel.send(embed=_build_welcome_embed(interaction.user))
        await interaction.response.send_message(
            f"✅ Wysłano testowe powitanie na {channel.mention}.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))
