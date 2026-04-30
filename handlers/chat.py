from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters
from database import Database
from config import LANG, AI_USER_ID
from .ai_handler import get_ai_response

db = Database()

async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # We only care about private messages
    if update.message.chat.type != 'private':
        return
        
    db_user = db.get_user(user_id)
    if db_user and db_user.get('is_banned'):
        return

    active_chat = db.get_active_chat(user_id)
    if not active_chat:
        # If they type random text but aren't in a chat, prompt them.
        await update.message.reply_text(LANG['no_active_chat'])
        return
        
    partner_id = db.get_chat_partner(active_chat, user_id)
    if not partner_id:
        return
        
    # Process referral if this is their first valid message
    referrer_to_notify = db.process_referral_reward(user_id)
    if referrer_to_notify:
        try:
            await context.bot.send_message(chat_id=referrer_to_notify, text="🎉 *Referral Success!*\n\nYour referred friend just sent their first message in a chat! You received *+100 Coins* and *$0.001*. 💵🪙", parse_mode="Markdown")
        except:
            pass
        
    # Handle AI Chat
    if active_chat.get('is_ai'):
        if not update.message.text:
            await update.message.reply_text("🤖 *AI Partner:* I only understand text for now!", parse_mode="Markdown")
            return
            
        # Log user message
        db.log_message(active_chat['id'], user_id, 'text', update.message.text)
        
        # Show "typing..."
        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        
        # Get chat history for context (last 10 messages)
        history = db.get_chat_history(active_chat['id'])
        ai_messages = []
        for h in history[-10:]:
            role = "user" if h['sender_id'] == user_id else "assistant"
            ai_messages.append({"role": role, "content": h['content']})
            
        # Get AI response
        ai_reply = await get_ai_response(ai_messages)
        
        # Send reply
        await update.message.reply_text(ai_reply)
        
        # Log AI response
        db.log_message(active_chat['id'], AI_USER_ID, 'text', ai_reply)
        return
        
    # Forward the message based on its type
    msg = update.message
    try:
        if msg.text:
            text = msg.text
            await context.bot.send_message(chat_id=partner_id, text=text)
            db.log_message(active_chat['id'], user_id, 'text', text)
            
        elif msg.sticker:
            sticker = msg.sticker.file_id
            await context.bot.send_sticker(chat_id=partner_id, sticker=sticker)
            db.log_message(active_chat['id'], user_id, 'sticker', sticker)
            
        else:
            # Check if sender is under a media ban
            if db.is_media_banned(user_id):
                await update.message.reply_text(
                    "🚫 *Media Restricted*\n\nYou have been reported for inappropriate media and are banned from sending media for 3 days.",
                    parse_mode="Markdown"
                )
                return

            # Secure Media Intercept
            media_type = "Media"
            is_voice = False
            if msg.photo: media_type = "Photo"
            elif msg.video: media_type = "Video"
            elif msg.voice: 
                media_type = "Voice Note"
                is_voice = True
            elif msg.audio: media_type = "Audio File"
            elif msg.document: media_type = "Document"
            elif msg.animation: media_type = "GIF"
            elif msg.video_note: media_type = "Video Note"
            
            # VIP Voice Bypass
            if is_voice and db_user.get('is_vip'):
                await context.bot.send_voice(chat_id=partner_id, voice=msg.voice.file_id)
                db.log_message(active_chat['id'], user_id, 'voice', msg.voice.file_id)
                return

            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Accept", callback_data=f"medacc_{user_id}_{msg.message_id}"),
                 InlineKeyboardButton("❌ Decline", callback_data=f"meddec_{user_id}_{msg.message_id}")]
            ])
            
            await context.bot.send_message(
                chat_id=partner_id, 
                text=f"⚠️ *Media Request*\n\nYour partner wants to send a *{media_type}*.\nDo you want to receive it?",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
            await update.message.reply_text(f"⏳ *Sent {media_type}.* Waiting for partner to accept it...", parse_mode="Markdown")
            db.log_message(active_chat['id'], user_id, 'media_request', str(msg.message_id))
            
    except Exception as e:
        print(f"Error forwarding message: {e}")
        db.end_chat(active_chat['id'])
        await update.message.reply_text("Partner disconnected.")
        try:
            await context.bot.send_message(chat_id=partner_id, text="Partner disconnected.")
        except:
            pass

def setup_chat_handler(application):
    # This must be the absolute lowest priority handler to not intercept commands or keyboard replies.
    # filters.ALL & ~filters.COMMAND & ~filters.Regex('^(...)$')
    chat_filter = filters.ALL & ~filters.COMMAND & ~filters.Regex('^(🔍 Find Partner|🛑 Stop Chat|⏭ Next Partner|👤 My Profile|💎 VIP Hub|⚙️ Settings|🎁 Rewards|📈 Stats|❓ Help)$')
    application.add_handler(MessageHandler(chat_filter, handle_chat_message))
