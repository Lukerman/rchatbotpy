from telegram import Update
from telegram.ext import ContextTypes, filters
from database import Database
from config import ADMIN_IDS

db = Database()

async def maintenance_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware-like handler to block non-admins during maintenance.
    Must be added to group -2 to run before regular handlers but after forced subscription.
    """
    user_id = update.effective_user.id
    
    # Admins always bypass
    if user_id in ADMIN_IDS:
        return
        
    bot_active = db.get_setting('bot_active', '1')
    if bot_active == '0':
        msg = db.get_setting('maintenance_message', '🛠 *Bot Maintenance*\n\nThe bot is currently undergoing maintenance. Please try again later.')
        
        if update.callback_query:
            await update.callback_query.answer(msg.replace('*', ''), show_alert=True)
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")
            
        # Stop further handling
        from telegram.ext import ApplicationHandlerStop
        raise ApplicationHandlerStop()

async def chat_cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for periodic cleanup task."""
    pass

async def scheduled_broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for scheduled broadcasts."""
    pass
