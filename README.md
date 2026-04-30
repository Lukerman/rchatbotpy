# Telegram Random Chat Bot (Python)

A fully-featured, highly scalable, and gamified Telegram Random Chat Bot built in Python 3 using `python-telegram-bot` (v21.1.1) and SQLite3. 

This project is a high-performance Python modernization of a legacy PHP random chat bot. It is designed to handle a large number of concurrent users seamlessly with advanced matchmaking algorithms, a comprehensive virtual economy, global interaction spaces, and automated content moderation.

---

## 🚀 Features

### 💬 Core Chat & Matchmaking
- **Anonymous Real-Time Matchmaking:** Users enter a queue and are instantly paired with strangers. Matches prioritize VIP users and join queue times.
- **Partner Preferences:** Users can set filters to search for specific genders (`Male`, `Female`, `Other`, `Any`).
- **Quick Navigation:** Standardized commands (`/search`, `/next`, `/stop`) to seamlessly jump between chats without lag.
- **Reconnect Protocol:** If a chat ends prematurely, users receive a prompt asking if they want to reconnect. If both accept, the session resumes.
- **Post-Chat Actions:** After a chat ends, users can rate their partner (1-5 Stars), block them permanently, or report them for misconduct.

### 💰 Economy, VIP & Gamification
- **Coins & Virtual Currency:** The core currency of the bot, earnable via chatting, referrals, daily streaks, or promo codes.
- **Daily Rewards Streak:** A scaled reward system. Logging in daily increases the coin payout (Day 1: 20 coins, Day 5+: 100 coins max).
- **VIP Accounts:** Users can purchase VIP status using their coins. VIP users receive queue priority and are shown their partner's profile stats (Age, Gender, Interests) before saying hello.
- **XP & Leveling System:** Users passively earn XP for chatting, increasing their level and public prestige.
- **Referral System:** Users possess unique referral links. When a new user joins via a link, both the referrer and the new user receive coin bonuses.
- **Promo Codes:** Integrated engine for issuing custom single-use or multi-use promo codes (e.g., granting VIP status or flat coin injections).

### 🌐 Social & Global Feed
- **Global Wall:** A public feed where users can broadcast messages to the entire community.
- **Interactions:** Other users can "Like" wall posts to boost their visibility or "Report" them if inappropriate.
- **Profiles & Statistics:** Users can maintain a public profile with their Age, Gender, and Interests, and track their global rank, top ratings, and total messages sent.

### 🛡 Moderation, Security & Anti-Abuse
- **Automated Anti-Spam:** strict cooldown timers and flood detection (`FLOOD_LIMIT` within a `FLOOD_WINDOW`) to prevent server overload and user harassment.
- **Auto-Bans:** If a user accumulates a specific number of reports across various chats, the system automatically intervenes and permanently bans them.
- **Media Moderation System:** Dedicated media reporting capabilities. Users sending unsolicited NSFW or malicious media can be instantly reported, leading to temporary global media restrictions (`media_ban_until`).
- **Community-Led Feed Moderation:** Wall posts that hit a specific threshold of reports are automatically deleted by the system.

### 💼 Admin Panel
- **Secure Access:** An inline admin dashboard (`/admin`) hardcoded to specific Telegram Admin User IDs.
- **Auditing & Control:** Admins can view basic bot stats, perform global message Broadcasts, manually Ban/Unban problematic users, and manipulate economy balances.

---

## 📂 Architecture and Codebase Structure

The bot uses the standard application builder paradigm of `python-telegram-bot`, modularized across several distinct handler files. 

```text
rchatbotpy/
│
├── main.py                # Application entry point & basic logging setup
├── config.py              # Configuration constants, timeouts, and ALL UI Language text strings
├── database.py            # SQLite3 Singleton logic & data schema
├── requirements.txt       # Dependencies (python-telegram-bot[job-queue]==21.1.1)
│
├── data/                  # Generates on first run containing 'bot.sqlite'
│
└── handlers/              # Modular Command & Callback logic
    ├── __init__.py        # Boots and registers all Conversation/Callback handlers
    ├── admin.py           # Dashboard rendering, Broadcasting, and manual ban systems
    ├── chat.py            # The core message router processing real-time text/media between pairs
    ├── commands.py        # Generic start, rules, and stat queries
    ├── economy.py         # Shop processing, Promo code redemption, and Daily Streak scaling logic
    ├── feed.py            # Wall interactions, liking, pagination, and post creation
    ├── post_chat.py       # Post-chat inline keyboard generation (rating, reconnect logic, block)
    ├── profile.py         # Conversation state handlers for creating/updating the User Profile
    └── settings.py        # Partner preference filters
```

> **Performance Note**: The database is structured dynamically using `sqlite3`. It employs `PRAGMA journal_mode=WAL` (Write-Ahead Logging), ensuring non-blocking reads and concurrent scaling despite using local file-based storage.

---

## 🛠 Setup & Installation

### Requirements
- Python 3.9+
- A valid Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd rchatbotpy
   ```

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Environment:**
   Open `config.py` in your chosen text editor. You must adjust the following keys:
   - `BOT_TOKEN`: Insert your Bot API token.
   - `BOT_USERNAME`: The actual `@handle` of your bot.
   - `ADMIN_IDS`: A Python list containing your personal Telegram User ID (vital for `/admin` access).

4. **Run the Application:**
   ```bash
   python main.py
   ```
   *Note: Upon its first execution, the system will actively construct `data/bot.sqlite` and automatically run internal database migrations if needed.*

---

## ⚖️ License & Usage

This project contains proprietary architecture specifically designed for scalable Telegram interactions. Please contact the repository owner/author for distinct usage and distribution rights.
