from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import Database

db = Database()

GENDERS = {
    'any': '🌐 Any',
    'male': '👨 Male',
    'female': '👩 Female',
    'other': '🌈 Other'
}

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)

    # VIP gate
    if not user or not user.get('is_vip'):
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("💎 Get VIP", callback_data="shop_vip")
        ]])
        await update.message.reply_text(
            "⚙️ *Chat Settings*\n\n"
            "🔒 *This feature is for VIP members only.*\n\n"
            "VIP members can filter partners by gender, keeping your matches more relevant.\n\n"
            "Upgrade to 💎 VIP to unlock this and other premium perks!",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    current_pref = GENDERS.get(user.get('gender_pref', 'any'), '🌐 Any')
    current_reg = user.get('match_region', 'global').capitalize()

    text = (
        f"⚙️ *Chat Settings*\n\n"
        f"💎 VIP Member\n"
        f"• Gender Preference: {current_pref}\n"
        f"• Match Radius: {current_reg}\n\n"
        f"Adjust your preferences below:"
    )

    keyboard = [
        [InlineKeyboardButton("👨 Male", callback_data="setpref_male"),
         InlineKeyboardButton("👩 Female", callback_data="setpref_female")],
        [InlineKeyboardButton("🌈 Other", callback_data="setpref_other"),
         InlineKeyboardButton("🌐 Any", callback_data="setpref_any")],
        [InlineKeyboardButton("🏙️ City", callback_data="setreg_city"),
         InlineKeyboardButton("🏳️ Country", callback_data="setreg_country")],
        [InlineKeyboardButton("🌍 Global", callback_data="setreg_global")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    # Handle VIP upgrade shortcut from settings screen
    if query.data == "shop_vip":
        from handlers.economy import shop_command
        await shop_command(update, context)
        return

    if query.data.startswith("setpref_"):
        new_pref = query.data.split('_')[1]
        if new_pref in GENDERS:
            db.update_user(user_id, {'gender_pref': new_pref})
        
    elif query.data.startswith("setreg_"):
        new_reg = query.data.split('_')[1]
        db.update_user(user_id, {'match_region': new_reg})

        user = db.get_user(user_id)
        current_pref = GENDERS.get(user.get('gender_pref', 'any'), '🌐 Any')
        current_reg = user.get('match_region', 'global').capitalize()

        text = (
            f"⚙️ *Chat Settings*\n\n"
            f"💎 VIP Member\n"
            f"• Gender Preference: {current_pref}\n"
            f"• Match Radius: {current_reg}\n\n"
            f"✅ Preference updated!"
        )
        keyboard = [
            [InlineKeyboardButton("👨 Male", callback_data="setpref_male"),
             InlineKeyboardButton("👩 Female", callback_data="setpref_female")],
            [InlineKeyboardButton("🌈 Other", callback_data="setpref_other"),
             InlineKeyboardButton("🌐 Any", callback_data="setpref_any")],
            [InlineKeyboardButton("🏙️ City", callback_data="setreg_city"),
             InlineKeyboardButton("🏳️ Country", callback_data="setreg_country")],
            [InlineKeyboardButton("🌍 Global", callback_data="setreg_global")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
