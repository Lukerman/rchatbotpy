from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database import Database
from config import LANG
from handlers.admin import notify_ban

db = Database()

async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    parts = query.data.split('_')
    chat_id = int(parts[1])
    rating = int(parts[2])
    
    if db.has_rated(chat_id, user_id):
        await query.edit_message_text("✅ You have already rated this chat.")
        return
        
    # Safely fetch the chat dict then extract partner
    chat = db.get_active_chat(user_id) or db.get_chat_by_id(chat_id)
    if not chat:
        partner_id = db.get_user(user_id).get('last_partner_id')
    else:
        partner_id = db.get_chat_partner(chat, user_id)
        
    if partner_id:
        db.update_rating(partner_id, rating)
        db.set_chat_rated(chat_id, user_id)
        
        text = f"✅ Thanks for rating! ({rating} ⭐)"
        
        # Give some XP for rating
        db.add_xp(user_id, 10)
        
        # If rating is 4 or 5, reward the partner and offer reconnect
        if rating >= 4:
            db.add_coins(partner_id, 10)
            try:
                await context.bot.send_message(chat_id=partner_id, text="💰 *Chat Bonus!*\n\nYou received a high rating and earned +10 Coins!", parse_mode="Markdown")
            except:
                pass
            
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Reconnect", callback_data=f"reconnect_{partner_id}")]])
            await query.edit_message_text(text + "\n\nWould you like to reconnect with them?", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text)
    else:
        await query.edit_message_text("Error finding partner data.")

async def reconnect_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    target_id = int(query.data.split('_')[1])
    
    await query.answer("Request sent!")
    await query.edit_message_text("📩 Reconnect request sent! Waiting for partner's response...")
    
    try:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept", callback_data=f"reconnect_accept_{user_id}"),
             InlineKeyboardButton("❌ Decline", callback_data=f"reconnect_decline_{user_id}")]
        ])
        await context.bot.send_message(chat_id=target_id, text="🔄 Your previous partner wants to reconnect!\n\nWould you like to chat again?", reply_markup=markup)
    except:
        await query.edit_message_text("😔 Your partner is unreachable.")

async def reconnect_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    action = query.data.split('_')[1]
    requester_id = int(query.data.split('_')[2])
    
    await query.answer()
    if action == 'accept':
        # Check active chat
        if db.get_active_chat(user_id) or db.get_active_chat(requester_id):
            await query.edit_message_text("❌ One of you is already in a new chat.")
            return
            
        chat_id = db.create_chat(user_id, requester_id)
        await query.edit_message_text("🎉 *Reconnected!* You're chatting with your previous partner again.", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=requester_id, text="🎉 *Reconnected!* You're chatting with your previous partner again.", parse_mode="Markdown")
        except:
            pass
    else:
        await query.edit_message_text("You declined the reconnect request.")
        try:
            await context.bot.send_message(chat_id=requester_id, text="😔 Your partner declined the reconnect request.")
        except:
            pass

async def block_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    partner_id = int(query.data.split('_')[1])
    
    db.block_user(user_id, partner_id)
    await query.answer("User blocked.")
    await query.edit_message_text("🚫 *User blocked.* You won't be matched with them again.", parse_mode="Markdown")

async def report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Expect data: report_PARTNERID_CHATID
    parts = query.data.split('_')
    partner_id = int(parts[1])
    chat_id = int(parts[2])
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Spam", callback_data=f"rptsbmt_spam_{partner_id}_{chat_id}"),
         InlineKeyboardButton("Harassment", callback_data=f"rptsbmt_harassment_{partner_id}_{chat_id}")],
        [InlineKeyboardButton("Illegal Content", callback_data=f"rptsbmt_illegal_{partner_id}_{chat_id}"),
         InlineKeyboardButton("NSFW", callback_data=f"rptsbmt_nsfw_{partner_id}_{chat_id}")]
    ])
    
    await query.edit_message_text("⚠️ *Select Report Reason:*", reply_markup=markup, parse_mode="Markdown")

async def report_submit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    parts = query.data.split('_')
    reason = parts[1]
    partner_id = int(parts[2])
    chat_id = int(parts[3])
    
    is_banned = db.report_user(user_id, partner_id, chat_id, reason)
    await query.answer("Report submitted.")
    
    if is_banned:
        await notify_ban(context, partner_id)
        
    await query.edit_message_text("✅ *Report submitted.* Thank you for keeping our community safe.", parse_mode="Markdown")

# Commands for inside chat
async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_chat = db.get_active_chat(user_id)
    if not active_chat:
        user = db.get_user(user_id)
        if user and user.get('last_partner_id'):
            db.block_user(user_id, user['last_partner_id'])
            await update.message.reply_text("🚫 Previous partner blocked.")
        else:
            await update.message.reply_text("❌ Nobody to block.")
        return
        
    partner_id = db.get_chat_partner(active_chat, user_id)
    db.block_user(user_id, partner_id)
    db.end_chat(active_chat['id'])
    
    await update.message.reply_text("🚫 *User blocked.* Chat ended.", parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=partner_id, text="😔 *Your partner has left the chat.*", parse_mode="Markdown")
    except:
        pass

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_chat = db.get_active_chat(user_id)
    
    if not active_chat:
        user = db.get_user(user_id)
        chat_id = 0
        partner_id = user.get('last_partner_id') if user else None
    else:
        chat_id = active_chat['id']
        partner_id = db.get_chat_partner(active_chat, user_id)
        
    if not partner_id:
        await update.message.reply_text("❌ Nobody to report.")
        return
        
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Spam", callback_data=f"rptsbmt_spam_{partner_id}_{chat_id}"),
         InlineKeyboardButton("Harassment", callback_data=f"rptsbmt_harassment_{partner_id}_{chat_id}")],
        [InlineKeyboardButton("Illegal Content", callback_data=f"rptsbmt_illegal_{partner_id}_{chat_id}"),
         InlineKeyboardButton("NSFW", callback_data=f"rptsbmt_nsfw_{partner_id}_{chat_id}")]
    ])
    
    await update.message.reply_text("⚠️ *Select Report Reason:*", reply_markup=markup, parse_mode="Markdown")
    
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_chat = db.get_active_chat(user_id)
    if not active_chat:
        await update.message.reply_text("❌ You need an active chat to send a gift.")
        return
        
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌹 Rose (10 Coins)", callback_data="gift_rose_10")],
        [InlineKeyboardButton("☕ Coffee (20 Coins)", callback_data="gift_coffee_20")],
        [InlineKeyboardButton("💎 Diamond (100 Coins)", callback_data="gift_diamond_100")]
    ])
    await update.message.reply_text("🎁 *Send a Gift to your Partner*\n\nChoose an item below:", reply_markup=markup, parse_mode="Markdown")

async def gift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    active_chat = db.get_active_chat(user_id)
    if not active_chat:
        await query.edit_message_text("❌ You need an active chat to send a gift.")
        return
        
    partner_id = db.get_chat_partner(active_chat, user_id)
    
    parts = query.data.split('_')
    item = parts[1].capitalize()
    cost = int(parts[2])
    
    user = db.get_user(user_id)
    if user and user.get('coins', 0) >= cost:
        # Deduct coins
        db.add_coins(user_id, -cost)
        
        # Announce
        await query.edit_message_text(f"✅ Gift sent: {item}")
        
        emoji = "🌹" if item == "Rose" else ("☕" if item == "Coffee" else "💎")
        try:
            await context.bot.send_message(chat_id=partner_id, text=f"🎁 Your partner sent you a gift!\n\n{emoji} *{item}*", parse_mode="Markdown")
        except:
            pass
    else:
        await query.edit_message_text("❌ You don't have enough coins.")

async def media_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    parts = query.data.split('_')
    action = parts[0]
    sender_id = int(parts[1])
    message_id = int(parts[2])
    
    await query.answer()
    
    if action == 'medacc':
        await query.edit_message_text("✅ Media accepted.")
        # Notify sender
        try:
            await context.bot.send_message(chat_id=sender_id, text="✅ Partner accepted your media.")
        except:
            pass
            
        # Copy message (deliver the actual media)
        try:
            await context.bot.copy_message(chat_id=user_id, from_chat_id=sender_id, message_id=message_id)
            # After delivery, offer a report button
            report_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚩 Report Media", callback_data=f"medrep_{sender_id}_{message_id}")]
            ])
            await context.bot.send_message(
                chat_id=user_id,
                text="Was this media inappropriate?",
                reply_markup=report_markup
            )
        except Exception as e:
            await context.bot.send_message(chat_id=user_id, text="❌ Failed to load media. It may have been deleted.")
            
    elif action == 'meddec':
        await query.edit_message_text("❌ Media declined.")
        # Notify sender
        try:
            await context.bot.send_message(chat_id=sender_id, text="🚫 Partner declined your media request.")
        except:
            pass

async def media_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id  # the reporter (receiver of media request)
    parts = query.data.split('_')
    sender_id = int(parts[1])   # the person who sent the media
    
    if sender_id == user_id:
        await query.answer("❌ You cannot report yourself.", show_alert=True)
        return
    
    already_reported, count = db.report_media(user_id, sender_id)
    
    if already_reported:
        await query.answer("❌ You have already reported this user's media.", show_alert=True)
        return
    
    REPORT_THRESHOLD = 3
    if count >= REPORT_THRESHOLD:
        db.apply_media_ban(sender_id, days=3)
        await query.answer("🚩 Reported! This user has been media-banned for 3 days.", show_alert=True)
        try:
            await context.bot.send_message(
                chat_id=sender_id,
                text="🚫 *Media Sending Restricted*\n\nYou have received multiple reports for inappropriate media. You are banned from sending any media for *3 days*.",
                parse_mode="Markdown"
            )
        except:
            pass
    else:
        remaining = REPORT_THRESHOLD - count
        await query.answer(f"🚩 Reported! ({count}/{REPORT_THRESHOLD} reports)", show_alert=True)
    
    # Also decline the pending media to avoid it being forwarded after reporting
    await query.edit_message_text("🚩 *Media reported and declined.*\n\nThank you for keeping the community safe.", parse_mode="Markdown")
    try:
        await context.bot.send_message(chat_id=sender_id, text="🚫 Your media was reported and declined by your partner.")
    except:
        pass

async def save_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    parts = query.data.split('_')
    chat_id = int(parts[1])
    
    success, message = db.save_chat(user_id, chat_id, cost=50)
    
    if success:
        await query.answer(f"💾 {message}", show_alert=True)
        # Disable the button to prevent double-spending
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ *Chat Saved!*\n\nYou can view your saved conversations later in your profile.",
            parse_mode="Markdown"
        )
    else:
        await query.answer(f"❌ {message}", show_alert=True)
