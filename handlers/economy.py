from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import Database

db = Database()

# States for promo code conversation
PROMO_INPUT = 1

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success, result = db.claim_daily(user_id)
    
    if success:
        amount, streak = result
        await update.message.reply_text(f"🎁 *Daily Reward Claimed!*\n\n🔥 *Day {streak} Streak!*\nYou received +{amount} coins! Come back tomorrow to keep your streak alive.", parse_mode="Markdown")
    else:
        hours = result // 3600
        minutes = (result % 3600) // 60
        await update.message.reply_text(f"⏳ You must wait {hours}h {minutes}m before claiming your next reward.")

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    coins = user.get('coins', 0) if user else 0
    is_vip = user.get('is_vip', 0) if user else 0
    
    # Handle both direct message and callback query
    msg = update.message if update.message else update.callback_query.message
    
    if is_vip:
        await msg.reply_text("💎 *You are already a VIP member!* Enjoy your perks.", parse_mode="Markdown")
        return
        
    text = (
        f"╭─── 💎 𝐕𝐈𝐏 𝐇𝐮𝐛 ───\n"
        f"│ 💰 Your balance: {coins} coins\n"
        f"│ \n"
        f"│ 🌟 *VIP Perks:*\n"
        f"│ - Priority Matching\n"
        f"│ - See Partner's Age/Gender immediately\n"
        f"│ - Unique Badge\n"
        f"╰──────────────────────\n\n"
        f"Price: *500 Coins* for Lifetime VIP"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Buy Lifetime VIP (500 Coins)", callback_data="buy_vip_500")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await msg.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    if query.data == "buy_vip_500":
        user = db.get_user(user_id)
        if user and user.get('coins', 0) >= 500:
            success = db.purchase_vip(user_id, 500)
            if success:
                await query.edit_message_text("🎉 *Congratulations!* You are now a Lifetime VIP.", parse_mode="Markdown")
            else:
                await query.edit_message_text("❌ An error occurred processing your purchase.")
        else:
            await query.edit_message_text("❌ You don't have enough coins! Use /daily to earn more.")

# --- Promo Code Conversation ---

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎫 *Promo Code*\n\nPlease enter your promo code:", parse_mode="Markdown")
    return PROMO_INPUT

async def promo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip()
    
    result = db.redeem_promo(user_id, code)
    
    if result == 'invalid':
        await update.message.reply_text("❌ Invalid promo code.")
    elif result == 'expired':
        await update.message.reply_text("❌ This promo code has expired or reached its max uses.")
    elif result == 'already_used':
        await update.message.reply_text("❌ You have already redeemed this promo code.")
    else:
        # Success result is now a dictionary
        promo_type = result.get('type')
        if promo_type == 'coins':
            amount = result.get('amount', 0)
            await update.message.reply_text(f"✅ Success! You received {amount} coins.", parse_mode="Markdown")
        elif promo_type == 'vip':
            await update.message.reply_text(f"✅ Success! You received VIP status.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"✅ Success! Promo code redeemed.", parse_mode="Markdown")
            
    return ConversationHandler.END

async def cancel_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Promo redemption cancelled.")
    return ConversationHandler.END
