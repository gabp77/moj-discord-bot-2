"""Komendy moderacyjne / narzędziowe: /say, /clear."""
import discord
from discord import app_commands
from discord.ext import commands


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="say", description="Wysyła wiadomość przez bota.")
    @app_commands.describe(
        message="Treść wiadomości.",
        channel="Kanał docelowy (domyślnie bieżący).",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def say(
        self,
        interaction: discord.Interaction,
        message: str,
        channel: discord.TextChannel = None,
    ):
        target = channel or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Mogę pisać tylko na kanały tekstowe.", ephemeral=True
            )
            return
        await target.send(message, allowed_mentions=discord.AllowedMentions.none())
        await interaction.response.send_message(
            f"✅ Wysłano na {target.mention}.", ephemeral=True
        )

    @app_commands.command(name="clear", description="Usuwa N ostatnich wiadomości (1-100).")
    @app_commands.describe(amount="Liczba wiadomości do usunięcia (1-100).")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Działa tylko na kanałach tekstowych.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await channel.purge(limit=amount)
        await interaction.followup.send(
            f"🧹 Usunięto **{len(deleted)}** wiadomości.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
