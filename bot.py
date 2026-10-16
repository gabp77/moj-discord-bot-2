"""
Główny plik bota Discord.
Uruchom:  python bot.py
Token przechowywany w zmiennej środowiskowej DISCORD_TOKEN (plik .env).
"""
import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Konfiguracja środowiska
# ---------------------------------------------------------------------------
load_dotenv(Path(__file__).parent / ".env")

TOKEN = os.environ.get("DISCORD_TOKEN")
GUILD_ID = os.environ.get("GUILD_ID")  # opcjonalne — szybka synchronizacja slash

if not TOKEN:
    raise RuntimeError(
        "Brak zmiennej DISCORD_TOKEN. Utwórz plik .env na podstawie .env.example "
        "i wklej token bota."
    )

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Intents — włączone te potrzebne do powitań i ticketów
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.members = True          # wymagane do on_member_join (włącz też w Dev Portal!)
intents.message_content = True  # na wszelki wypadek dla komend tekstowych


class TicketBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",  # nieużywane — korzystamy ze slashy
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        # Ładujemy wszystkie cogi
        for cog in ("cogs.tickets", "cogs.general", "cogs.moderation", "cogs.welcome"):
            await self.load_extension(cog)
            log.info("Loaded cog: %s", cog)

        # Rejestrujemy persistent view (przyciski kategorii + close) — przeżyją restart
        from cogs.tickets import TicketPanelView, CloseTicketView
        self.add_view(TicketPanelView())
        self.add_view(CloseTicketView())

        # Synchronizacja slash
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d slash commands to guild %s", len(synced), GUILD_ID)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global slash commands (może zająć do 1h)", len(synced))

    async def on_ready(self) -> None:
        log.info("Bot zalogowany jako %s (ID: %s)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Game(name="/setup-tickets  •  gotowy do zgłoszeń")
        )


async def main() -> None:
    bot = TicketBot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot zatrzymany.")
