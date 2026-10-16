"""Komendy ogólne: /ping, /userinfo, /serverinfo."""
import time

import discord
from discord import app_commands
from discord.ext import commands


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Sprawdza opóźnienie bota.")
    async def ping(self, interaction: discord.Interaction):
        start = time.perf_counter()
        await interaction.response.defer(ephemeral=True)
        rt = (time.perf_counter() - start) * 1000
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.blurple())
        embed.add_field(name="API Latency", value=f"`{self.bot.latency * 1000:.0f} ms`")
        embed.add_field(name="Round-trip", value=f"`{rt:.0f} ms`")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="userinfo", description="Pokazuje informacje o użytkowniku.")
    @app_commands.describe(user="Użytkownik, o którym chcesz uzyskać informacje. Domyślnie Ty.")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        embed = discord.Embed(
            title=f"Informacje o {user}",
            color=user.color if user.color.value else discord.Color.blurple(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=False)
        embed.add_field(name="Konto utworzone", value=discord.utils.format_dt(user.created_at, "R"))
        if isinstance(user, discord.Member) and user.joined_at:
            embed.add_field(name="Dołączył/a", value=discord.utils.format_dt(user.joined_at, "R"))
        if isinstance(user, discord.Member):
            roles = [r.mention for r in user.roles if r.name != "@everyone"]
            embed.add_field(
                name=f"Role ({len(roles)})",
                value=" ".join(roles) if roles else "Brak",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="serverinfo", description="Pokazuje informacje o serwerze.")
    async def serverinfo(self, interaction: discord.Interaction):
        g = interaction.guild
        embed = discord.Embed(title=g.name, color=discord.Color.blurple())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="ID", value=f"`{g.id}`")
        embed.add_field(name="Właściciel", value=g.owner.mention if g.owner else "—")
        embed.add_field(name="Utworzony", value=discord.utils.format_dt(g.created_at, "R"))
        embed.add_field(name="Członkowie", value=str(g.member_count))
        embed.add_field(name="Kanały", value=str(len(g.channels)))
        embed.add_field(name="Role", value=str(len(g.roles)))
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
