from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from database import Database

import requests
db = Database()

GENDER, AGE, LOCATION, INTERESTS = range(4)

async def reverse_geocode(lat, lon):
    """Simple reverse geocoding using Nominatim (OSM)."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=en"
        headers = {'User-Agent': 'TelegramChatBot/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        address = data.get('address', {})
        city = address.get('city') or address.get('town') or address.get('village') or address.get('suburb') or ''
        country = address.get('country', '')
        return city, country
    except Exception as e:
        print(f"Geocoding error: {e}")
        return '', ''

async def edit_profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("👨 Male", callback_data="prof_male"), InlineKeyboardButton("👩 Female", callback_data="prof_female")],
        [InlineKeyboardButton("🌈 Other", callback_data="prof_other"), InlineKeyboardButton("⏭ Skip", callback_data="prof_skip")]
    ]
    await query.edit_message_text("👤 *Profile Setup (1/4)*\n\nPlease select your gender:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard), 
                                  parse_mode="Markdown")
    return GENDER

async def profile_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    data = query.data.split('_')[1]
    if data != 'skip':
        db.update_user(user_id, {'gender': data})
        
    await query.edit_message_text("🎂 *Profile Setup (2/4)*\n\nPlease type your age (e.g., 22)\n\nOr click Skip below:",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Skip", callback_data="prof_skip")]]),
                                  parse_mode="Markdown")
    return AGE
    
async def profile_age_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if text.isdigit():
        age = int(text)
        if 13 <= age <= 99:
            db.update_user(user_id, {'age': age})
            await update.message.reply_text(
                "📍 *Profile Setup (3/4)*\n\nPlease share your location using the button below to find nearby partners:\n\n(Or click Skip if you prefer to remain global)",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📍 Share Location", callback_data="prof_loc_req")],
                    [InlineKeyboardButton("⏭ Skip", callback_data="prof_skip")]
                ]),
                parse_mode="Markdown"
            )
            return LOCATION
            
    await update.message.reply_text("❌ Please enter a valid age between 13 and 99.")
    return AGE
    
async def profile_age_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📍 *Profile Setup (3/4)*\n\nPlease share your location using the button below to find nearby partners:\n\n(Or click Skip if you prefer to remain global)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📍 Share Location", callback_data="prof_loc_req")],
            [InlineKeyboardButton("⏭ Skip", callback_data="prof_skip")]
        ]),
        parse_mode="Markdown"
    )
    return LOCATION

async def profile_location_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This handles the 'Share Location' button click in the inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    # We can't request location via InlineButton directly in a useful way for setup flow
    # unless we use a ReplyKeyboardMarkup temporarily.
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    markup = ReplyKeyboardMarkup([
        [KeyboardButton("📍 Share My Location", request_location=True)],
        [KeyboardButton("⏭ Skip")]
    ], resize_keyboard=True, one_time_keyboard=True)
    
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Please click the Share button below or hit Skip to continue without location:",
        reply_markup=markup
    )
    return LOCATION

async def profile_location_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    loc = update.message.location
    text = update.message.text
    
    from telegram import ReplyKeyboardRemove
    if loc:
        print(f"DEBUG: Received location {loc.latitude}, {loc.longitude} from user {user_id}")
        city, country = await reverse_geocode(loc.latitude, loc.longitude)
        print(f"DEBUG: Geocoded to {city}, {country}")
        db.update_location(user_id, loc.latitude, loc.longitude, country, city)
        loc_str = f"{city}, {country}" if city else country
        await update.message.reply_text(f"✅ Location set to: *{loc_str}*", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    elif text == "⏭ Skip":
        await update.message.reply_text("⏩ Location skipped.", reply_markup=ReplyKeyboardRemove())
    else:
        # If they type something else, just treat it as a skip for now to avoid getting stuck
        await update.message.reply_text("⏩ Moving to next step.", reply_markup=ReplyKeyboardRemove())
        
    await update.message.reply_text("🎯 *Profile Setup (4/4)*\n\nPlease type your interests, separated by commas (e.g., music, games, movies)\n\nOr click Skip to finish:",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Skip", callback_data="prof_skip")]]),
                                  parse_mode="Markdown")
    return INTERESTS

async def profile_location_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎯 *Profile Setup (4/4)*\n\nPlease type your interests, separated by commas (e.g., music, games, movies)\n\nOr click Skip to finish:",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Skip", callback_data="prof_skip")]]),
                                  parse_mode="Markdown")
    return INTERESTS

async def profile_interests_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    db.update_user(user_id, {'interests': text[:100]}) # Limit length
    await update.message.reply_text("✅ *Profile Setup Complete!*\n\nUse /profile to view it.", parse_mode="Markdown")
    return ConversationHandler.END
    
async def profile_interests_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ *Profile Setup Complete!*\n\nUse /profile to view it.", parse_mode="Markdown")
    return ConversationHandler.END

async def cancel_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Profile setup cancelled.")
    return ConversationHandler.END
