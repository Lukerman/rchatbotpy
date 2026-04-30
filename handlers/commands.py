from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import Database
from config import LANG, AI_SEARCH_DELAY as FALLBACK_DELAY, AI_USER_ID, BOT_USERNAME

from .economy import daily_command, shop_command
from .settings import settings_command
db = Database()

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🔍 Find Partner"), KeyboardButton("🛑 Stop Chat")],
        [KeyboardButton("🌐 Global Feed"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("👤 My Profile"), KeyboardButton("📈 Stats")],
        [KeyboardButton("🎁 Rewards"), KeyboardButton("💸 Refer & Earn")],
        [KeyboardButton("💎 VIP Hub")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_chat_keyboard():
    keyboard = [
        [KeyboardButton("🛑 Stop Chat"), KeyboardButton("⏭ Next Partner")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_search_keyboard():
    keyboard = [
        [KeyboardButton("🛑 Stop Chat")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref_code = context.args[0] if context.args else None
    
    # create_user will handle referral reward internally if the user is completely new
    db_user = db.create_user(user.id, user.username or '', user.first_name, user.last_name or '', referred_code=ref_code)
    
    # Check if they were a new user with a valid referrer
    if ref_code and db_user and db_user.get('referred_by'):
        try:
            await update.message.reply_text("🎁 *Welcome Bonus!*\n\nYou joined using a referral link and received +20 Coins!", parse_mode="Markdown")
        except:
            pass
                 
    # Check ban
    if db_user and db_user.get('is_banned'):
        await update.message.reply_text(LANG['banned'])
        return
        
    await update.message.reply_text(LANG['welcome'], parse_mode='Markdown', reply_markup=get_main_keyboard())

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check if banned
    db_user = db.get_user(user_id)
    if db_user and db_user.get('is_banned'):
         await update.message.reply_text(LANG['banned'])
         return
         
    # Cleanup old messages before searching
    db.cleanup_user_chats(user_id)
         
    # Check if gender is set
    if not db_user or not db_user.get('gender'):
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("✏️ Setup Profile", callback_data="edit_profile")]])
        await update.message.reply_text("⚠️ *Profile Required*\n\nYou must select your gender before you can start searching for a partner. Please set up your profile first.", reply_markup=markup, parse_mode="Markdown")
        return
         
    # Check if already in chat
    active_chat = db.get_active_chat(user_id)
    if active_chat:
        await update.message.reply_text(LANG['already_in_chat'])
        return
        
    # Check if already in queue
    if db.is_in_queue(user_id):
        await update.message.reply_text(LANG['already_searching'])
        return

    # Try to find match
    match = db.find_match(user_id)
    if match:
        partner_id = match['user_id']
        chat_id = db.create_chat(user_id, partner_id)
        
        # Notify both users
        try:
            await update.message.reply_text(LANG['partner_found'], reply_markup=get_chat_keyboard(), parse_mode='Markdown')
            await context.bot.send_message(chat_id=partner_id, text=LANG['partner_found'], reply_markup=get_chat_keyboard(), parse_mode='Markdown')
        except Exception as e:
            print(f"Error notifying partner: {e}")
            db.end_chat(chat_id)
            await update.message.reply_text("Partner disconnected. Please search again.")
    else:
        db.add_to_queue(user_id, db_user.get('gender_pref', 'any') if db_user else 'any')
        await update.message.reply_text(LANG['searching'], reply_markup=get_search_keyboard(), parse_mode='Markdown')
        
        # Schedule AI fallback
        delay = int(db.get_setting('ai_search_delay', FALLBACK_DELAY))
        context.job_queue.run_once(
            ai_fallback_job, 
            when=delay, 
            data={'user_id': user_id, 'chat_id': update.effective_chat.id},
            name=f"ai_fallback_{user_id}"
        )

async def ai_fallback_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Check if user is still in queue
    if db.is_in_queue(user_id):
        # Create AI chat
        db.create_ai_chat(user_id)
        
        try:
            await context.bot.send_message(
                chat_id=chat_id, 
                text=LANG['partner_found'], 
                reply_markup=get_chat_keyboard(), 
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error notifying user of AI match: {e}")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # If in queue, remove
    if db.is_in_queue(user_id):
        db.remove_from_queue(user_id)
        await update.message.reply_text("Search cancelled.", reply_markup=get_main_keyboard())
        return
        
    active_chat = db.get_active_chat(user_id)
    if not active_chat:
        await update.message.reply_text(LANG['no_active_chat'], reply_markup=get_main_keyboard())
        return
        
    db.end_chat(active_chat['id'], user_id)
    partner_id = db.get_chat_partner(active_chat, user_id)
    
    # Send rating & reconnect inline keyboard to user
    rate_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 1", callback_data=f"rate_{active_chat['id']}_1"),
         InlineKeyboardButton("⭐⭐ 2", callback_data=f"rate_{active_chat['id']}_2"),
         InlineKeyboardButton("⭐⭐⭐ 3", callback_data=f"rate_{active_chat['id']}_3")],
        [InlineKeyboardButton("⭐⭐⭐⭐ 4", callback_data=f"rate_{active_chat['id']}_4"),
         InlineKeyboardButton("🌟🌟🌟🌟🌟 5", callback_data=f"rate_{active_chat['id']}_5")],
        [InlineKeyboardButton("🚫 Block", callback_data=f"block_{partner_id}"),
         InlineKeyboardButton("⚠️ Report", callback_data=f"report_{partner_id}_{active_chat['id']}")],
        [InlineKeyboardButton("💾 Save Chat (50 Coins)", callback_data=f"savechat_{active_chat['id']}")]
    ])
    
    await update.message.reply_text(LANG['chat_ended'] + "\n\n⭐ *Please rate your partner and chat:*", reply_markup=rate_markup, parse_mode='Markdown')
    if partner_id:
        try:
            partner_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ 1", callback_data=f"rate_{active_chat['id']}_1"),
                 InlineKeyboardButton("⭐⭐ 2", callback_data=f"rate_{active_chat['id']}_2"),
                 InlineKeyboardButton("⭐⭐⭐ 3", callback_data=f"rate_{active_chat['id']}_3")],
                [InlineKeyboardButton("⭐⭐⭐⭐ 4", callback_data=f"rate_{active_chat['id']}_4"),
                 InlineKeyboardButton("🌟🌟🌟🌟🌟 5", callback_data=f"rate_{active_chat['id']}_5")],
                [InlineKeyboardButton("🚫 Block", callback_data=f"block_{user_id}"),
                 InlineKeyboardButton("⚠️ Report", callback_data=f"report_{user_id}_{active_chat['id']}")],
                [InlineKeyboardButton("💾 Save Chat (50 Coins)", callback_data=f"savechat_{active_chat['id']}")]
            ])
            await context.bot.send_message(chat_id=partner_id, text=LANG['chat_ended_by_partner'] + "\n\n⭐ *Please rate your partner and chat:*", reply_markup=partner_markup, parse_mode='Markdown')
            # Follow up with main keyboard for partner
            await context.bot.send_message(chat_id=partner_id, text="Options:", reply_markup=get_main_keyboard())
        except:
            pass
            
    # Follow up with main keyboard for user
    await update.message.reply_text("Options:", reply_markup=get_main_keyboard())

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_chat = db.get_active_chat(user_id)
    if active_chat:
        db.end_chat(active_chat['id'], user_id)
        # We don't cleanup here yet, because the user might report in the post-chat menu.
        partner_id = db.get_chat_partner(active_chat, user_id)
        if partner_id:
            try:
                await context.bot.send_message(chat_id=partner_id, text=LANG['chat_ended_by_partner'], reply_markup=get_main_keyboard(), parse_mode='Markdown')
            except:
                pass
                
    if db.is_in_queue(user_id):
        db.remove_from_queue(user_id)
        
    await search_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LANG['help'], parse_mode='Markdown')

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LANG['rules'], parse_mode='Markdown')

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check for new achievements
    new_achs = db.check_achievements(user_id)
    if new_achs:
        for ach in new_achs:
            await update.message.reply_text(f"🏆 *Achievement Unlocked!*\n\nYou earned the `{ach.replace('_', ' ').title()}` badge!", parse_mode="Markdown")

    user = db.get_user(user_id)
    if user:
        bot_user = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_user.username}?start={user.get('referral_code', 'error')}"
        
        # Earned Badges display
        achs = db.get_user_achievements(user_id)
        badge_map = {
            'social_butterfly': '🦋',
            'talkative': '🦜',
            'coin_collector': '💰',
            'guardian': '🛡️',
            'veteran': '🎖️'
        }
        badges_str = " ".join([badge_map.get(a['achievement_type'], '🏅') for a in achs])
        if not badges_str: badges_str = "None"

        loc_val = f"{user.get('city')}, {user.get('country')}" if user.get('city') else (user.get('country') or 'Not set')
        
        text = LANG['profile_view'] % (
            user.get('gender') or 'Not set',
            user.get('age') or 'Not set',
            loc_val,
            user.get('interests') or 'None',
            user.get('coins') or 0,
            f"{user.get('rating_sum') / max(user.get('rating_count') or 1, 1):.1f}",
            user.get('total_chats') or 0,
            user.get('created_at') or 'Unknown',
            ref_link
        )
        text += f"\n🏆 *Achievements:* {badges_str}"
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Edit Profile", callback_data="edit_profile")],
            [InlineKeyboardButton("📂 View Saved Chats", callback_data="saved_list")]
        ])
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_top_users(10)
    text = "🏆 *Global Leaderboard*\n\n"
    for i, u in enumerate(users):
        name = u.get('first_name') or u.get('username') or 'Unknown'
        text += f"{i+1}. {name} - Lvl {u.get('level')} ({u.get('xp')} XP)\n"
    await update.message.reply_text(text, parse_mode='Markdown')

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    ref = user.get('referral_code') if user else 'N/A'
    bot_user = await context.bot.get_me()
    text = f"🔗 *Your Referral Link*\n\nShare this link to earn rewards!\n`https://t.me/{bot_user.username}?start={ref}`\n\n💰 *Benefits:*\n• You get: *100 Coins* + *$0.001*\n• Your friend gets: *20 Coins*\n\n_Note: You receive your reward when your friend sends their first message in a chat!_"
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if user:
        ref_count, ref_earnings, cash_earnings = db.get_referral_stats(user_id)
        text = LANG['stats_view'] % (
            user.get('total_chats') or 0,
            user.get('total_messages') or 0,
            ref_count,
            ref_earnings,
            cash_earnings,
            user.get('rating_sum') / max(user.get('rating_count') or 1, 1),
            user.get('level') or 1
        )
        await update.message.reply_text(text, parse_mode='Markdown')

# Keyboard command router
async def keyboard_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔍 Find Partner":
        await search_command(update, context)
    elif text == "🛑 Stop Chat":
        await stop_command(update, context)
    elif text == "🌐 Global Feed":
        from .feed import feed_command
        await feed_command(update, context)
    elif text == "👤 My Profile":
        await profile_command(update, context)
    elif text == "❓ Help":
        await help_command(update, context)
    elif text == "📈 Stats":
        await stats_command(update, context)
    elif text == "🎁 Rewards":
        await daily_command(update, context)
    elif text == "💸 Refer & Earn":
        await refer_command(update, context)
    elif text == "💎 VIP Hub":
        await shop_command(update, context)
    elif text == "⚙️ Settings":
        await settings_command(update, context)
    else:
        # If not a recognized keyboard button, maybe it's a message for their partner?
        # That will be handled by the chat handler which needs to be priority/fallback.
        pass

def setup_command_handlers(application):
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('search', search_command))
    application.add_handler(CommandHandler('stop', stop_command))
    application.add_handler(CommandHandler('next', next_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('rules', rules_command))
    application.add_handler(CommandHandler('profile', profile_command))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('top', top_command))
    application.add_handler(CommandHandler('refer', refer_command))
    
    # Catch keyboard replies specifically if they match those emojis
    application.add_handler(MessageHandler(filters.Regex('^(🔍 Find Partner|🛑 Stop Chat|⏭ Next Partner|👤 My Profile|💎 VIP Hub|⚙️ Settings|🎁 Rewards|📈 Stats|🌐 Global Feed|💸 Refer & Earn)$'), keyboard_router))
