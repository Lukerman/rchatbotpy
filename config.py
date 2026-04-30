import os
import json
from dotenv import load_dotenv


load_dotenv()


def _clean_env(value):
    """Normalize placeholder-like env values used by some deployment UIs."""
    if value is None:
        return None
    cleaned = str(value).strip()
    if cleaned in {"", "/", "null", "None", "NONE"}:
        return None
    return cleaned


def _env_or_default(name, default=None):
    value = _clean_env(os.getenv(name))
    return default if value is None else value


def _parse_admin_ids(default_ids):
    raw = _clean_env(os.getenv("ADMIN_IDS"))
    if raw is None:
        return default_ids

    # Accept JSON list ("[1,2]") or CSV ("1,2") for deployment UI compatibility.
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [int(x) for x in parsed]
    except Exception:
        pass

    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def _load_lang(default_lang):
    raw = _clean_env(os.getenv("LANG"))
    if raw is None:
        return default_lang

    # Accept simple language code (currently "en") or a JSON dict override.
    if raw.lower() in {"en", "en-us", "en_gb", "english"}:
        return default_lang

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
        
    # Fallback to default if it's not a valid JSON dict (e.g., standard OS locales like 'en_US.UTF-8')
    return default_lang

# ==================== BOT SETTINGS ====================
BOT_TOKEN = _env_or_default('BOT_TOKEN', '')
BOT_USERNAME = _env_or_default('BOT_USERNAME', 'RandomChatsss_Bot')
# Change this for webhook or leave as None for polling locally
WEBHOOK_URL = None

# ==================== ADMIN SETTINGS ====================
ADMIN_IDS = _parse_admin_ids([])
ADMIN_PASSWORD = _env_or_default('ADMIN_PASSWORD', '')

# ==================== FORCE SUBSCRIBE ====================
FORCE_SUB_CHANNEL_ID = -1003906769086
FORCE_SUB_LINK = 'https://t.me/RandomChatsssBotupdate' # Update this link!

# ==================== DATABASE ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'bot.sqlite')

# ==================== MATCHING SETTINGS ====================
QUEUE_TIMEOUT = 300           # Seconds before removing from queue (5 min)
SEARCH_COOLDOWN = 3           # Seconds between search attempts
MIN_CHAT_DURATION = 0         # Min seconds before rating prompt
AI_SEARCH_DELAY = 3           # Seconds to wait before connecting to AI

# ==================== ANTI-SPAM ====================
FLOOD_LIMIT = 30              # Max messages per window
FLOOD_WINDOW = 60             # Window in seconds
MESSAGE_COOLDOWN = 0.5        # Min seconds between messages
MAX_MESSAGE_LENGTH = 4096     # Max text message length

# ==================== VIP SETTINGS ====================
VIP_PRIORITY_BOOST = True
VIP_SEE_PARTNER_INFO = True

# ==================== MISC ====================
LOG_MESSAGES = True
ENABLE_RATING = True
ENABLE_RECONNECT = True
MAX_REPORTS_BEFORE_BAN = 5
BOT_VERSION = '1.0.0'

# ==================== AI SETTINGS ====================
AI_PROVIDER = "openrouter" # Options: "openrouter", "dashscope"
OPENROUTER_API_KEY = _env_or_default('OPENROUTER_API_KEY', '')
DASHSCOPE_API_KEY = _env_or_default('DASHSCOPE_API_KEY', '') # Add your DashScope API Key here
AI_USER_ID = 1  # Reserved ID for AI partner
AI_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
AI_SYSTEM_PROMPT = """
You are a casual user on a random chat app (like OmeTV or Chatroulette).
- Be informal and use natural human conversational style.
- Use modern internet slang occasionally but don't overdo it.
- Keep your responses relatively short (1-3 sentences).
- If asked personal questions, give realistic but generic answers (e.g., "I'm from NYC", "Just chilling").
- Never mention that you are an AI or a bot.
- Do not use punctuation like a professional; keep it casual.
- Your goal is to keep the conversation going like a normal person would.
"""

# ==================== TEXT STRINGS ====================
LANG = {
    'welcome': "╭─── ✨ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐑𝐚𝐧𝐝𝐨𝐦 𝐂𝐡𝐚𝐭 ───\n│ Connect with thousands of users\n│ completely anonymously in seconds.\n╰──────────────────────────────\n\n🚀 *Quick Start:*\nHit 🔍 *Find Partner* below to jump into the queue!\n\n📖 *Commands:*\n• /search — Find partner\n• /stop — End chat\n• /next — Skip partner\n• /help — More features",
    
    'help': "📖 *Available Commands*\n\n🔍 /search — Find a random partner\n🛑 /stop — End current conversation\n⏭ /next — End current & find new\n👤 /profile — View/edit your profile\n⚙️ /settings — Set partner preferences\n📈 /stats — Your chat statistics\n🚫 /block — Block current partner\n⚠️ /report — Report current partner\n📋 /rules — Community guidelines\n❓ /help — This help message",
    
    'rules': "📋 *Community Rules*\n\n1️⃣ Be respectful to everyone\n2️⃣ No spam or flooding\n3️⃣ No sharing personal info of others\n4️⃣ No illegal content\n5️⃣ No harassment or hate speech\n6️⃣ No advertising\n7️⃣ No NSFW content\n8️⃣ Report violations\n\n⚠️ *Violating rules may result in a permanent ban.*",
    
    'searching': "🚀 *Searching for a partner...*\n\nFinding the perfect match for you in the queue.\nSend /stop to cancel.",
    
    'partner_found': "🎉 *Partner found!*\n\nYou're now securely connected. Say Hello! 👋\n\n*Options:*\n🛑 /stop to end • ⏭ /next for new partner",
    
    'partner_found_vip': "🎉 *Partner found!*\n\n╭─── 👤 𝐏𝐚𝐫𝐭𝐧𝐞𝐫 𝐈𝐧𝐟𝐨 ───\n│ 💠 Gender: %s\n│ 💠 Age: %s\n│ 💠 Interests: %s\n╰──────────────────────\n\n*Options:*\n🛑 /stop to end • ⏭ /next for new partner",
    
    'chat_ended': "👋 *Chat ended.*\n\nSend /search to jump back in.",
    
    'chat_ended_by_partner': "😔 *Your partner has left the chat.*\n\nSend /search to find someone new.",
    
    'no_active_chat': "❌ You don't have an active chat.\n\nHit 🔍 Find Partner to get started.",
    
    'already_in_chat': "💬 You're already in a conversation!\n\nSend /stop to end it first.",
    
    'already_searching': "🚀 You're already in the matchmaking queue!\n\nPlease wait or send /stop to cancel.",
    
    'banned': "🚫 You have been permanently banned.\n\nContact an admin if you think this is a mistake.",
    
    'flood_warning': "⚠️ *Slow down!* You're sending messages too fast.",
    
    'report_sent': "✅ *Report submitted.*\nThank you for keeping our community safe.",
    
    'report_reason': "⚠️ *Report Partner*\n\nPlease select the exact reason below:",
    
    'blocked': "🚫 *User blocked.*\nYou will never be matched with them again.",
    
    'profile_view': "╭─── 👤 𝐘𝐨𝐮𝐫 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 ───\n│ 💠 Gender: %s\n│ 💠 Age: %s\n│ 📍 Location: %s\n│ 💠 Interests: %s\n│ \n│ 💰 Balance: %d Coins\n│ ⭐ Rating: %s (Max 5.0)\n│ 💬 Total Chats: %d\n╰───────────────────────\n\n*Date Joined:* %s\n\n🔗 *Your Referral Link:*\n`%s`",
    
    'profile_set_gender': "👤 *Set your gender:*",
    
    'profile_set_age': "🎂 *Enter your age:*\n\n(Send a number between 13 and 99)",
    
    'profile_set_interests': "🎯 *Set your interests:*\n\nSend your interests separated by commas.\nExample: music, gaming, movies, sports",
    
    'settings_view': "⚙️ *Chat Settings*\n\n• Preferred Gender: %s\n\nTap below to change your matchmaking filters:",
    
    'pref_set': "✅ Preference secured!",
    
    'stats_view': "╭─── 📈 𝐘𝐨𝐮𝐫 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬 ───\n│ 💬 Total Chats: %d\n│ 📨 Messages Sent: %d\n│ 👥 Users Referred: %d\n│ 💰 Referral Earnings: %d Coins & $%.3f\n│ \n│ ⭐ Rating: %s\n│ 🏆 Global Rank: %s\n╰────────────────────────",
    
    'rate_partner': "⭐ *Rate your partner:*\n\nHow was your conversation?",
    
    'rating_thanks': "✅ Thanks for your feedback! (%d ⭐)",
    
    'reconnect_ask': "🔄 Would you like to reconnect with your previous partner?",
    
    'reconnect_sent': "📩 Reconnect request broadcasted! Waiting for partner's response...",
    
    'reconnect_received': "🔄 Your previous partner has requested to reconnect!\n\nWould you like to chat again?",
    
    'reconnect_accepted': "🎉 *Reconnected!* Welcome back to your conversation.",
    
    'reconnect_declined': "😔 Your partner politely declined the reconnect request.",
    
    'no_one_found': "😔 *No one found right now.*\n\nYou've been placed in the priority queue. We'll alert you silently when a match is found!\n\nSend /stop to cancel.",

    'gender_male': '👨 Male',
    'gender_female': '👩 Female',
    'gender_other': '🌈 Other',
    'gender_any': '🌐 Any',
    'gender_not_set': '⚠️ Not set',
    
    'admin_broadcast_done': "✅ Broadcast successfully executed to %d users.",
    'admin_ban': "✅ User %s has been banned.",
    'admin_unban': "✅ User %s has been successfully unbanned.",
    'ban_notification': "🚫 *You have been permanently banned.* \nContact an admin if you think this is a mistake.",
    'report_success_notification': "✅ *Action Taken:* A user you reported has been banned. Thank you for helping keep the community safe!",
    'unban_notification': "✅ *Good news!* Your account has been unbanned. You can now use the bot again. Hit /search to find a partner!",
    'report_dismissed_notification': "ℹ️ *Report Update:* Your report has been reviewed by admins. After investigation, we found no violation of our rules. Thank you for helping keep the community safe!",

    'force_sub_msg': "⚠️ *Subscription Required*\n\nTo use this bot, you must be a member of our official channel. Join now and click 'I have joined' below!",
    'force_sub_button': "📢 Join Channel",
    'force_sub_check': "✅ I have joined",
    'force_sub_joined': "🎉 Thank you for joining! You can now use the bot.",

    'profile_setup_loc': "📍 *Profile Setup (3/4)*\n\nSharing your location allows the bot to find partners in your **City** or **Country** first.\n\nYour exact coordinates are never shown to others.",
    'feed_title': "╭─── 🌐 𝐆𝐥𝐨𝐛𝐚𝐥 𝐅𝐞𝐞𝐝 ({offset + 1}/{total_posts}) ───\n",
    'feed_cat_trending': "🔥 Trending",
    'feed_cat_new': "🆕 Newest",
    'feed_cat_nearby': "📍 Nearby",
}

# Optional deployment override for localization map or language code.
LANG = _load_lang(LANG)
