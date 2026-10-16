# 🤖 Discord Ticket Bot (Python)

Bot Discord z panelem ticketów, prywatnymi kanałami, komendami slash i powitaniem nowych członków.
Napisany w **Python 3.10+** z użyciem [`discord.py`](https://discordpy.readthedocs.io/).

> 🔐 **Token bota NIGDY nie jest w kodzie.** Trzymamy go w pliku `.env` (lub zmiennej środowiskowej u hostingodawcy).

---

## ✨ Funkcje

| Funkcja | Opis |
|---|---|
| 🎫 **Panel ticketów** | Komenda `/setup-tickets` wysyła wiadomość z menu wyboru kategorii. |
| 📂 **4 kategorie zgłoszeń** | Pomoc techniczna · Zgłoszenie gracza · Pytanie ogólne · Współpraca |
| 🔒 **Prywatne kanały** | Każdy ticket to osobny kanał widoczny tylko dla autora, admina i (opcjonalnie) roli zespołu. |
| 🧨 **Przycisk zamknięcia** | Czerwony przycisk „Zamknij ticket" + slash `/close`. |
| 👋 **Powitania** | Nowi członkowie dostają piękny embed z avatarem na konfigurowalnym kanale. |
| ⚡ **Slash commands** | `/ping`, `/userinfo`, `/serverinfo`, `/say`, `/clear`, `/add-user`, `/remove-user`, `/set-welcome-channel`, `/test-welcome`. |
| ♻️ **Persistent views** | Przyciski i menu działają również po restarcie bota. |

---

## 🚀 Szybki start

### 1. Utwórz aplikację Discord
1. Wejdź na https://discord.com/developers/applications → **New Application**.
2. Zakładka **Bot** → **Reset Token** → **skopiuj token** (zobaczysz go tylko raz!).
3. W sekcji **Privileged Gateway Intents** włącz:
   - ✅ **Server Members Intent** (potrzebne do powitań)
   - ✅ **Message Content Intent** (dla pewności)
4. Zakładka **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Manage Channels`, `Manage Messages`, `Send Messages`, `Embed Links`,
     `Read Message History`, `View Channels`, `Mention Everyone`
5. Otwórz wygenerowany link i zaproś bota na swój serwer.

### 2. Zainstaluj zależności
```bash
cd /app/bot
pip install -r requirements.txt
```

### 3. Skonfiguruj token
```bash
cp .env.example .env
# otwórz .env i wklej token w DISCORD_TOKEN
```

Opcjonalnie uzupełnij:
- `GUILD_ID` – ID Twojego serwera testowego (slashe pojawią się natychmiast).
- `TICKETS_CATEGORY_ID` – ID kategorii, w której mają powstawać kanały ticketów.
- `STAFF_ROLE_ID` – ID roli zespołu (automatycznie dostanie dostęp do każdego ticketu).
- `WELCOME_CHANNEL_ID` – ID kanału powitań (lub ustaw przez `/set-welcome-channel`).

> Jak znaleźć ID? W Discordzie: **Ustawienia użytkownika → Zaawansowane → Tryb dewelopera**.
> Potem kliknij prawym na serwer/kanał/rolę → **Kopiuj ID**.

### 4. Uruchom bota
```bash
python bot.py
```

Powinieneś zobaczyć:
```
Loaded cog: cogs.tickets
Loaded cog: cogs.general
Loaded cog: cogs.moderation
Loaded cog: cogs.welcome
Synced 11 slash commands to guild ...
Bot zalogowany jako TicketBot#1234 (ID: ...)
```

### 5. Postaw panel ticketów
Na serwerze wpisz:
```
/setup-tickets channel:#support
```
Gotowe! Użytkownicy wybierają kategorię z dropdownu, a bot tworzy prywatny kanał.

---

## 📜 Lista komend

### 🎫 Tickety
| Komenda | Opis | Uprawnienie |
|---|---|---|
| `/setup-tickets [channel]` | Wysyła panel wyboru kategorii. | `Manage Server` |
| `/close` | Zamyka bieżący ticket. | Autor / Staff / Admin |
| `/add-user <user>` | Dodaje użytkownika do ticketu. | Wewnątrz ticketu |
| `/remove-user <user>` | Usuwa użytkownika z ticketu. | Wewnątrz ticketu |

### 👋 Powitania
| Komenda | Opis | Uprawnienie |
|---|---|---|
| `/set-welcome-channel <channel>` | Ustawia kanał powitań. | `Manage Server` |
| `/test-welcome` | Wysyła testowe powitanie. | `Manage Server` |

### 🛠️ Ogólne / moderacja
| Komenda | Opis | Uprawnienie |
|---|---|---|
| `/ping` | Opóźnienie bota. | wszyscy |
| `/userinfo [user]` | Info o użytkowniku. | wszyscy |
| `/serverinfo` | Info o serwerze. | wszyscy |
| `/say <message> [channel]` | Bot wysyła wiadomość. | `Manage Messages` |
| `/clear <1-100>` | Czyści ostatnie wiadomości. | `Manage Messages` |

---

## 📂 Struktura projektu
```
bot/
├── bot.py                 # entrypoint, ładowanie cogów, sync slashy
├── requirements.txt
├── .env.example           # szablon zmiennych środowiskowych
├── .gitignore
└── cogs/
    ├── __init__.py
    ├── tickets.py         # panel, kategorie, prywatne kanały, close
    ├── welcome.py         # on_member_join + /set-welcome-channel
    ├── general.py         # /ping, /userinfo, /serverinfo
    ├── moderation.py      # /say, /clear
    └── storage.py         # lekki storage JSON (per-guild)
```

---

## 🌐 Hosting — gdzie uruchomić bota?

Nie wiesz co wybrać? Oto najprostsze opcje:

| Opcja | Dla kogo | Jak |
|---|---|---|
| **Twój komputer** | Testy, mały serwer | `python bot.py` — bot działa dopóki okno jest otwarte. |
| **Railway.app** | Hobby, darmowe limity | Wrzuć repo, w zakładce *Variables* dodaj `DISCORD_TOKEN`. |
| **Replit** | Zero konfiguracji | New Repl → Python → wklej kod → **Secrets** → `DISCORD_TOKEN`. |
| **VPS (DigitalOcean, Hetzner)** | 24/7 niezawodnie | `screen`/`tmux` lub `systemd` + `.env`. |
| **Docker** | Powtarzalny deploy | Zbuduj obraz z `python:3.11-slim` + `pip install -r requirements.txt`. |

Niezależnie od wyboru — **token zawsze w zmiennej środowiskowej / sekrecie, nigdy w kodzie.**

---

## 🔒 Bezpieczeństwo

- Plik `.env` **nie trafia** do repozytorium (jest w `.gitignore`).
- Jeśli token wyciekł — natychmiast kliknij **Reset Token** w panelu dewelopera Discord.
- Bot nie zapisuje treści wiadomości na dysk.
