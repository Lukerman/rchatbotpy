from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from database import Database
from config import LANG

db = Database()

async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a request for the user's location."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    # VIP check (Optional: matching by location can be VIP, but setting location for all?)
    # Since matching prioritize city/country, let's allow all to set it, but VIPs control the radius.
    
    markup = ReplyKeyboardMarkup([
        [KeyboardButton("📍 Share My Location", request_location=True)],
        [KeyboardButton("❌ Cancel")]
    ], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "📍 *Update Your Location*\n\n"
        "Sharing your location allows the bot to find partners in your **City** or **Country** first.\n\n"
        "Your exact coordinates are never shown to other users.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the shared location and updates the DB."""
    user_id = update.effective_user.id
    location = update.message.location
    
    if location:
        # We don't have built-in reverse geocoding without external API keys.
        # For now, we store lat/long. 
        # Future expansion could use geopy or a public API to get City/Country.
        db.update_location(user_id, location.latitude, location.longitude)
        
        await update.message.reply_text(
            "✅ *Location Updated!*\n\n"
            "The bot will now prioritize matching you with nearby users.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Failed to get location.", reply_markup=ReplyKeyboardRemove())
