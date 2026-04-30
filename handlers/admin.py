import time
import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from config import ADMIN_IDS, LANG

db = Database()

# States for Admin Conversation
(
    BROADCAST_MSG,
    BAN_USER,
    UNBAN_USER,
    COINS_USER,
    COINS_AMT,
    USER_LOOKUP,
    CONFIG_MESS,
    PROMO_CODE,
    PROMO_AMT,
    PROMO_LIMIT
) = range(101, 111)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    await _show_dashboard(update, context)

async def _show_dashboard(update, context):
    users, active, queue = db.get_global_stats()
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Manage User", callback_data="adm_usr_search"),
         InlineKeyboardButton("📢 Broadcast", callback_data="adm_bcast")],
        [InlineKeyboardButton("🎫 Promo Manager", callback_data="adm_promo_hub"),
         InlineKeyboardButton("⚙️ Bot Configs", callback_data="adm_config_hub")],
        [InlineKeyboardButton("🌐 Feed Manager", callback_data="adm_feed_0"),
         InlineKeyboardButton("📈 Refresh", callback_data="adm_dash")],
        [InlineKeyboardButton("❌ Close", callback_data="adm_close")]
    ])

    text = (
        "╭─── 🛡️ 𝐀𝐝𝐦𝐢𝐧 𝐃𝐚𝐬𝐡𝐛𝐨𝐚𝐫𝐝 ───\n"
        f"│ 👥 Total Users: {users}\n"
        f"│ 💬 Active Chats: {active}\n"
        f"│ ⏳ Queue Size: {queue}\n"
        "╰────────────────────────"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.answer("Unauthorized.", show_alert=True)
        return

    await query.answer()
    data = query.data

    if data == "adm_dash":
        await _show_dashboard(update, context)
        return ConversationHandler.END

    elif data == "adm_usr_search":
        await query.edit_message_text("🔍 *User Lookup*\n\nEnter the Telegram User ID to manage:", parse_mode="Markdown")
        return USER_LOOKUP

    elif data == "adm_bcast":
        await query.edit_message_text("📢 *Global Broadcast*\n\nEnter message (Markdown):", parse_mode="Markdown")
        return BROADCAST_MSG

    elif data == "adm_config_hub":
        await _show_config_hub(update, context)
        return ConversationHandler.END

    elif data == "adm_promo_hub":
        await _show_promo_hub(update, context)
        return ConversationHandler.END
        
    elif data == "adm_close":
        await query.edit_message_text("✅ Admin panel closed.")
        return ConversationHandler.END

    return ConversationHandler.END

# --- USER MANAGEMENT ---
async def admin_user_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(update.message.text.strip())
        user = db.get_user_detailed(target_id)
        if not user:
            await update.message.reply_text("❌ User not found.")
            return ConversationHandler.END
            
        await _show_user_panel(update, context, user)
    except ValueError:
        await update.message.reply_text("❌ Invalid ID.")
    return ConversationHandler.END

async def _show_user_panel(update, context, user):
    is_banned = user.get('is_banned', 0)
    is_vip = user.get('is_vip', 0)
    
    status_emoji = "🚫 Banned" if is_banned else "✅ Active"
    vip_emoji = "💎 VIP" if is_vip else "👤 Free"
    
    text = (
        f"👤 *User Profile: {user['user_id']}*\n"
        f"• Name: {user['first_name']} {user.get('last_name', '')}\n"
        f"• Status: {status_emoji} | {vip_emoji}\n"
        f"• Coins: {user.get('coins', 0)} | XP: {user.get('xp', 0)}\n"
        f"• Joined: {user.get('joined_date', 'N/A')}\n"
        f"• Location: {user.get('city', 'N/A')}, {user.get('country', 'N/A')}"
    )
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban/Unban", callback_data=f"admusr_ban_{user['user_id']}"),
         InlineKeyboardButton("💎 Toggle VIP", callback_data=f"admusr_vip_{user['user_id']}")],
        [InlineKeyboardButton("💰 Grant Coins", callback_data=f"admusr_coin_{user['user_id']}"),
         InlineKeyboardButton("« Back", callback_data="adm_dash")]
    ])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")

async def admin_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split('_')
    action = parts[1]
    target_id = int(parts[2])
    
    user = db.get_user(target_id)
    if not user:
        await query.answer("User vanished!")
        return
        
    if action == 'ban':
        new_val = 0 if user['is_banned'] else 1
        db.update_user(target_id, {'is_banned': new_val})
        await query.answer(f"Status Updated: {'Banned' if new_val else 'Restored'}")
    elif action == 'vip':
        new_val = 0 if user['is_vip'] else 1
        db.update_user(target_id, {'is_vip': new_val})
        await query.answer(f"VIP Status: {'Granted' if new_val else 'Revoked'}")
    elif action == 'coin':
        context.user_data['adm_coin_target'] = target_id
        await query.edit_message_text(f"💰 How many coins to add to `{target_id}`?", parse_mode="Markdown")
        return COINS_AMT

    updated_user = db.get_user_detailed(target_id)
    await _show_user_panel(update, context, updated_user)

# --- CONFIG HUB ---
async def _show_config_hub(update, context):
    bot_active = db.get_setting('bot_active', '1')
    status_text = "🟢 Active" if bot_active == '1' else "🔴 Maintenance"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Toggle: {status_text}", callback_data="admcfg_toggle_active")],
        [InlineKeyboardButton("✍️ Edit Maint. Message", callback_data="admcfg_edit_msg")],
        [InlineKeyboardButton("« Back", callback_data="adm_dash")]
    ])
    
    await update.callback_query.edit_message_text("⚙️ *Bot Configurations*", reply_markup=markup, parse_mode="Markdown")

async def admin_config_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        data = query.data
        if data == "admcfg_toggle_active":
            curr = db.get_setting('bot_active', '1')
            new_val = '0' if curr == '1' else '1'
            db.set_setting('bot_active', new_val)
            await _show_config_hub(update, context)
        elif data == "admcfg_edit_msg":
            await query.edit_message_text("✍️ Send new maintenance message (Markdown):")
            return CONFIG_MESS
    else:
        # Handling text input for message
        new_msg = update.message.text
        db.set_setting('maintenance_message', new_msg)
        await update.message.reply_text("✅ Maintenance message updated.")
        return ConversationHandler.END

# --- PROMO HUB ---
async def _show_promo_hub(update, context):
    promos = db.get_all_promos()
    text = "🎫 *Promo Manager*\n\n"
    
    rows = []
    for p in promos[:8]: # Show top 8
        text += f"• `{p['code']}` ({p['type']}) - {p['current_uses']}/{p['max_uses']} uses\n"
        rows.append([InlineKeyboardButton(f"🗑 {p['code']}", callback_data=f"admpr_del_{p['code']}")])
        
    rows.append([InlineKeyboardButton("➕ Create Code", callback_data="admpr_new")])
    rows.append([InlineKeyboardButton("« Back", callback_data="adm_dash")])
    
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")

async def admin_promo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("admpr_del_"):
        code = data.split("_")[2]
        db.delete_promo(code)
        await _show_promo_hub(update, context)
    elif data == "admpr_new":
        await query.edit_message_text("🎫 Enter new code name (e.g. WELCOME2024):")
        return PROMO_CODE

async def admin_promo_input_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_promo_data'] = {'code': update.message.text.upper()}
    await update.message.reply_text("Select Type:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Coins", callback_data="admpr_type_coins"),
         InlineKeyboardButton("VIP", callback_data="admpr_type_vip")]
    ]))
    return PROMO_AMT

async def admin_promo_input_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        context.user_data['new_promo_data']['type'] = query.data.split("_")[2]
        await query.edit_message_text("💰 Enter amount (Coins) or days (VIP):")
    else:
        context.user_data['new_promo_data']['amount'] = int(update.message.text)
        await update.message.reply_text("🔢 Enter max uses (limit):")
        return PROMO_LIMIT

async def admin_promo_input_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = int(update.message.text)
        data = context.user_data['new_promo_data']
        db.create_promo_admin(data['code'], data['type'], data.get('amount', 0), limit)
        await update.message.reply_text(f"✅ Code `{data['code']}` created!")
    except:
        await update.message.reply_text("❌ Error creating code.")
    return ConversationHandler.END

# --- OTHER PLACEHOLDERS ---
async def admin_broadcast_msg(update, context):
    # Reuse existing broadcast logic but keep in conversation context
    msg = update.message.text
    user_ids = db.get_active_user_ids()
    await update.message.reply_text(f"⏳ Broadcasting to {len(user_ids)} users...")
    success = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 *Announcement*\n\n{msg}", parse_mode="Markdown")
            success += 1
        except: pass
    await update.message.reply_text(f"✅ Broadcast complete. {success} reached.")
    return ConversationHandler.END

async def admin_ban_user(u, c): pass
async def admin_unban_user(u, c): pass
async def admin_coins_user(u, c): pass
async def admin_coins_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get('adm_coin_target')
    try:
        amt = int(update.message.text.strip())
        db.add_coins(target, amt)
        await update.message.reply_text(f"✅ Added `{amt}` coins to User `{target}`.")
    except: pass
    return ConversationHandler.END

async def cancel_admin(u, c):
    await u.message.reply_text("Action cancelled.")
    return ConversationHandler.END

async def notify_ban(context, user_id):
    try: await context.bot.send_message(chat_id=user_id, text=LANG['ban_notification'], parse_mode="Markdown")
    except: pass

async def notify_unban(context, user_id):
    try: await context.bot.send_message(chat_id=user_id, text=LANG['unban_notification'], parse_mode="Markdown")
    except: pass
