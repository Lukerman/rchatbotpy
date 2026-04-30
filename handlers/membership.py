from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ApplicationHandlerStop
from config import FORCE_SUB_CHANNEL_ID, FORCE_SUB_LINK, LANG, ADMIN_IDS

async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if a user is subscribed to the required channel."""
    # Admins are exempt
    if user_id in ADMIN_IDS:
        return True
        
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL_ID, user_id=user_id)
        # Statuses that count as 'joined'
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        # If bot is not admin in channel or channel doesn't exist, we might get an error.
        # Log it and optionally allow use or block. 
        # For security, we usually block or let it pass if it's a bot configuration error.
        print(f"Error checking membership for {user_id}: {e}")
        # If we can't check, we might want to let it pass to avoid blocking everyone if the bot is broken.
        # But for 'force sub', the user usually wants it strict.
        # For now, let's assume if we can't check, they aren't 'subscribed'. 
        return False
        
    return False

async def subscription_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    High-priority middleware handler that intercepts all updates.
    Checks if the user is subscribed to the required channel.
    """
    user = update.effective_user
    if not user:
        return

    # Check if this is a callback for the 'I have joined' button
    if update.callback_query and update.callback_query.data == "check_sub":
        # Don't block the check itself!
        return

    # Skip for these updates (e.g. status changes, etc) if needed
    # But for private chats, we want to block everything.
    if update.effective_chat and update.effective_chat.type != 'private':
        return

    if not await is_user_subscribed(user.id, context):
        # User is NOT subscribed. Show the prompt.
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(LANG['force_sub_button'], url=FORCE_SUB_LINK)],
            [InlineKeyboardButton(LANG['force_sub_check'], callback_data="check_sub")]
        ])
        
        # If it's a callback query (e.g. button click), we should answer it or edit message
        if update.callback_query:
            await update.callback_query.answer("⚠️ You must join the channel first!", show_alert=True)
            # We can also update the message if it's not already the join prompt
            # but usually raising ApplicationHandlerStop is enough.
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text=LANG['force_sub_msg'],
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
        # Stop further processing of this update
        raise ApplicationHandlerStop()

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'I have joined' button click."""
    query = update.callback_query
    user_id = query.from_user.id
    
    if await is_user_subscribed(user_id, context):
        await query.answer(LANG['force_sub_joined'], show_alert=True)
        # Delete the join prompt and send welcome/start msg
        await query.message.delete()
        # Optionally trigger start command or just let them know they can now use the bot
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ *Access Granted!*\n\nYou can now use all the bot's features. Try /search to find a partner!",
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ You haven't joined the channel yet. Please join and try again.", show_alert=True)
