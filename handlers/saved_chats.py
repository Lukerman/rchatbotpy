from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import Database
from datetime import datetime

db = Database()

async def saved_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists saved chat sessions for the user."""
    user_id = update.effective_user.id
    
    c = db.conn.cursor()
    c.execute("""
        SELECT chat_id, originally_sent_at, count(*) as msg_count 
        FROM saved_messages 
        WHERE user_id = ? 
        GROUP BY chat_id 
        ORDER BY originally_sent_at DESC
    """, (user_id,))
    saved = c.fetchall()
    
    if not saved:
        text = "📂 *You have no saved chats yet.*\n\nTo save a chat, use the button at the end of a session (50 Coins)."
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
        return
        
    text = "📂 *Your Saved Chats*\n\nTap a session to view the transcript:"
    keyboard = []
    for row in saved:
        dt = datetime.fromtimestamp(row['originally_sent_at']).strftime('%Y-%m-%d %H:%M')
        label = f"📝 Chat {dt} ({row['msg_count']} msgs)"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"viewsaved_{row['chat_id']}")])
        
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def view_saved_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the transcript of a specific saved chat."""
    query = update.callback_query
    user_id = update.effective_user.id
    chat_id = int(query.data.split('_')[1])
    
    await query.answer()
    
    c = db.conn.cursor()
    c.execute("""
        SELECT sender_id, message_type, content, originally_sent_at 
        FROM saved_messages 
        WHERE user_id = ? AND chat_id = ? 
        ORDER BY originally_sent_at ASC
    """, (user_id, chat_id))
    messages = c.fetchall()
    
    if not messages:
        await query.edit_message_text("❌ Could not load this chat.")
        return
        
    transcript = f"📑 *Chat Transcript ({datetime.fromtimestamp(messages[0]['originally_sent_at']).strftime('%Y-%m-%d')})*\n\n"
    
    for msg in messages:
        sender_label = "👤 You" if msg['sender_id'] == user_id else "👤 Partner"
        if msg['message_type'] == 'text':
            transcript += f"*{sender_label}:* {msg['content']}\n"
        else:
            transcript += f"*{sender_label}:* [{msg['message_type']}]\n"
            
    # If transcript is too long, we might need to send it in chunks. 
    # For now, we'll try to send it in one message.
    if len(transcript) > 4000:
        transcript = transcript[:3900] + "\n\n... (Transcript truncated)"
        
    back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to List", callback_data="saved_list")]])
    await query.edit_message_text(transcript, reply_markup=back_markup, parse_mode="Markdown")
