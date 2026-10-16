"""
Panel ticketów: wybór kategorii z dropdownu -> prywatny kanał -> przycisk zamknięcia.
Wszystkie Views są persistent (custom_id) — przeżywają restart bota.
"""
import os
import re
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

# ---------------------------------------------------------------------------
# Konfiguracja kategorii zgłoszeń
# ---------------------------------------------------------------------------
TICKET_CATEGORIES = [
    {
        "value": "tech",
        "label": "Pomoc techniczna",
        "emoji": "🛠️",
        "description": "Problemy z serwerem, botem, konfiguracją.",
        "color": discord.Color.blurple(),
    },
    {
        "value": "report",
        "label": "Zgłoszenie gracza",
        "emoji": "🚨",
        "description": "Zgłoś łamanie regulaminu lub nadużycie.",
        "color": discord.Color.red(),
    },
    {
        "value": "question",
        "label": "Pytanie ogólne",
        "emoji": "❓",
        "description": "Nie wiesz jak coś działa? Zapytaj!",
        "color": discord.Color.green(),
    },
    {
        "value": "partnership",
        "label": "Współpraca",
        "emoji": "🤝",
        "description": "Propozycja partnerstwa lub współpracy.",
        "color": discord.Color.gold(),
    },
]

CATEGORY_BY_VALUE = {c["value"]: c for c in TICKET_CATEGORIES}

_INVALID_CHAN_CHARS = re.compile(r"[^a-z0-9\-]")


def _slug(name: str) -> str:
    name = name.lower().replace(" ", "-")
    name = _INVALID_CHAN_CHARS.sub("", name)
    return name[:80] or "user"


async def _get_tickets_category(guild: discord.Guild) -> Optional[discord.CategoryChannel]:
    cat_id = os.environ.get("TICKETS_CATEGORY_ID")
    if cat_id:
        cat = guild.get_channel(int(cat_id))
        if isinstance(cat, discord.CategoryChannel):
            return cat
    return None


def _staff_role(guild: discord.Guild) -> Optional[discord.Role]:
    role_id = os.environ.get("STAFF_ROLE_ID")
    if role_id:
        return guild.get_role(int(role_id))
    return None


# ---------------------------------------------------------------------------
# Dropdown panelu ticketów  (persistent)
# ---------------------------------------------------------------------------
class TicketCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=c["label"],
                value=c["value"],
                description=c["description"],
                emoji=c["emoji"],
            )
            for c in TICKET_CATEGORIES
        ]
        super().__init__(
            placeholder="📩 Wybierz kategorię zgłoszenia…",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="ticket_panel:select_category",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        category_value = self.values[0]
        category = CATEGORY_BY_VALUE[category_value]
        guild = interaction.guild
        user = interaction.user

        # Zapobiegamy duplikatom — jeden otwarty ticket na użytkownika
        existing = discord.utils.find(
            lambda c: isinstance(c, discord.TextChannel)
            and c.topic
            and f"ticket-owner:{user.id}" in c.topic,
            guild.channels,
        )
        if existing:
            await interaction.followup.send(
                f"❗ Masz już otwarty ticket: {existing.mention}",
                ephemeral=True,
            )
            return

        # Uprawnienia kanału
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                read_message_history=True,
            ),
        }
        staff_role = _staff_role(guild)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
            )

        parent = await _get_tickets_category(guild)
        channel_name = f"ticket-{category_value}-{_slug(user.name)}"

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=parent,
                topic=f"ticket-owner:{user.id} | kategoria:{category_value}",
                reason=f"Ticket otwarty przez {user} ({category['label']})",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Nie mam uprawnień do tworzenia kanałów. "
                "Nadaj mi rolę z `Manage Channels`.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"{category['emoji']}  {category['label']}",
            description=(
                f"Witaj {user.mention}! 👋\n\n"
                f"Opisz dokładnie swoją sprawę. Zespół odpowie najszybciej jak to możliwe.\n\n"
                f"Gdy skończysz — użyj przycisku **Zamknij ticket** poniżej."
            ),
            color=category["color"],
        )
        embed.set_footer(text=f"Ticket utworzony przez {user}", icon_url=user.display_avatar.url)

        mentions = user.mention
        if staff_role:
            mentions = f"{user.mention} {staff_role.mention}"

        await channel.send(
            content=mentions,
            embed=embed,
            view=CloseTicketView(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        await interaction.followup.send(
            f"✅ Twój ticket został utworzony: {channel.mention}",
            ephemeral=True,
        )
        # Reset selectu (żeby można było wybrać ponownie w przyszłości)
        # Nic nie musimy robić — persistent view zostanie zresetowany sam przy kolejnej interakcji.


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())


# ---------------------------------------------------------------------------
# Przycisk zamykania ticketu (persistent)
# ---------------------------------------------------------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Zamknij ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket:close",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not (channel.topic and "ticket-owner:" in channel.topic):
            await interaction.response.send_message(
                "❌ Ta komenda działa tylko wewnątrz kanału ticketu.", ephemeral=True
            )
            return

        # Weryfikacja uprawnień: autor ticketu, admin lub staff
        owner_id = _extract_owner_id(channel.topic)
        is_owner = owner_id == interaction.user.id
        is_admin = interaction.user.guild_permissions.manage_channels
        staff_role = _staff_role(interaction.guild)
        is_staff = staff_role in interaction.user.roles if staff_role else False

        if not (is_owner or is_admin or is_staff):
            await interaction.response.send_message(
                "❌ Tylko autor ticketu lub zespół może go zamknąć.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Ticket zostanie zamknięty za 5 sekund…", ephemeral=False
        )
        try:
            await channel.delete(reason=f"Ticket zamknięty przez {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Nie mam uprawnień do usunięcia kanału.", ephemeral=True
            )


def _extract_owner_id(topic: str) -> Optional[int]:
    match = re.search(r"ticket-owner:(\d+)", topic or "")
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------
class TicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setup-tickets",
        description="Wysyła panel ticketów (dropdown z kategoriami) na wskazany kanał.",
    )
    @app_commands.describe(channel="Kanał, na którym pojawi się panel. Domyślnie bieżący.")
    @app_commands.default_permissions(manage_guild=True)
    async def setup_tickets(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
    ):
        target = channel or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Panel można wysłać tylko na kanał tekstowy.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎫  Panel zgłoszeń",
            description=(
                "Potrzebujesz pomocy? Masz zgłoszenie? Wybierz **kategorię** z menu poniżej, "
                "a utworzymy prywatny kanał tylko dla Ciebie i naszego zespołu.\n\n"
                + "\n".join(
                    f"{c['emoji']}  **{c['label']}** — {c['description']}"
                    for c in TICKET_CATEGORIES
                )
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Jeden otwarty ticket na użytkownika.")

        await target.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message(
            f"✅ Panel ticketów wysłany na {target.mention}.", ephemeral=True
        )

    @app_commands.command(name="close", description="Zamyka bieżący ticket (usuwa kanał).")
    async def close(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not (channel.topic and "ticket-owner:" in channel.topic):
            await interaction.response.send_message(
                "❌ Tej komendy można użyć tylko w kanale ticketu.", ephemeral=True
            )
            return

        owner_id = _extract_owner_id(channel.topic)
        is_owner = owner_id == interaction.user.id
        is_admin = interaction.user.guild_permissions.manage_channels
        staff_role = _staff_role(interaction.guild)
        is_staff = staff_role in interaction.user.roles if staff_role else False
        if not (is_owner or is_admin or is_staff):
            await interaction.response.send_message(
                "❌ Tylko autor ticketu lub zespół może go zamknąć.", ephemeral=True
            )
            return

        await interaction.response.send_message("🔒 Zamykam ticket…")
        try:
            await channel.delete(reason=f"Ticket zamknięty przez {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Brak uprawnień do usunięcia kanału.", ephemeral=True)

    @app_commands.command(name="add-user", description="Dodaje użytkownika do bieżącego ticketu.")
    @app_commands.describe(user="Osoba, którą chcesz dodać.")
    async def add_user(self, interaction: discord.Interaction, user: discord.Member):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not (channel.topic and "ticket-owner:" in channel.topic):
            await interaction.response.send_message(
                "❌ Działa tylko wewnątrz kanału ticketu.", ephemeral=True
            )
            return
        await channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
        await interaction.response.send_message(f"✅ Dodano {user.mention} do ticketu.")

    @app_commands.command(name="remove-user", description="Usuwa użytkownika z bieżącego ticketu.")
    @app_commands.describe(user="Osoba, którą chcesz usunąć.")
    async def remove_user(self, interaction: discord.Interaction, user: discord.Member):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not (channel.topic and "ticket-owner:" in channel.topic):
            await interaction.response.send_message(
                "❌ Działa tylko wewnątrz kanału ticketu.", ephemeral=True
            )
            return
        owner_id = _extract_owner_id(channel.topic)
        if owner_id == user.id:
            await interaction.response.send_message(
                "❌ Nie można usunąć właściciela ticketu.", ephemeral=True
            )
            return
        await channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(f"✅ Usunięto {user.mention} z ticketu.")


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketsCog(bot))
