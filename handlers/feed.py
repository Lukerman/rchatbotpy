import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database import Database

db = Database()

FEED_POST_INPUT = 201

# --- VIEWING THE FEED ---
async def feed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_feed_page(update, context, offset=0, mode='trending')

async def send_feed_page(update: Update, context: ContextTypes.DEFAULT_TYPE, offset=0, mode='trending'):
    viewer_id = update.effective_user.id
    posts = db.get_wall_posts(offset=offset, limit=1, mode=mode, viewer_id=viewer_id)
    total_posts = db.get_wall_post_count()
    
    if not posts:
        text = "📭 *The Global Feed is empty.*\n\nBe the first to post something!"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("✍️ Create Post (25 Coins)", callback_data="fd_create")]])
    else:
        post = posts[0]
        elapsed = int(time.time()) - post['created_at']
        if elapsed < 60:
            time_str = "just now"
        elif elapsed < 3600:
            time_str = f"{elapsed // 60}m ago"
        elif elapsed < 86400:
            time_str = f"{elapsed // 3600}h ago"
        else:
            time_str = f"{elapsed // 86400}d ago"
            
        gender_emoji = "🚹" if post['gender'] == 'male' else ("🚺" if post['gender'] == 'female' else "🎭")
        loc_str = f"📍 {post['city']}, {post['country']}" if post['city'] else (f"📍 {post['country']}" if post['country'] else "📍 Global")
        vip_tag = " [💎 VIP]" if post['is_vip'] else ""
        
        text = (
            f"╭─── 🌐 𝐆𝐥𝐨𝐛𝐚𝐥 𝐅𝐞𝐞𝐝 ({offset + 1}/{total_posts}) ───\n"
            f"│ {gender_emoji} Anonymous User{vip_tag}\n"
            f"│ {loc_str}\n│ \n"
            f"│ \"{post['content']}\"\n│ \n"
            f"│ ❤️ {post['likes']} Likes       ⏱ {time_str}\n"
            f"╰────────────────────────"
        )
        
        # Category header buttons
        cat_row = [
            InlineKeyboardButton(("🔥 " if mode == 'trending' else "") + "Trending", callback_data="fd_cat_trending"),
            InlineKeyboardButton(("🆕 " if mode == 'new' else "") + "Newest", callback_data="fd_cat_new"),
            InlineKeyboardButton(("📍 " if mode == 'nearby' else "") + "Nearby", callback_data="fd_cat_nearby")
        ]

        nav_row = []
        if offset > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"fd_pg_{mode}_{offset-1}"))
        nav_row.append(InlineKeyboardButton("❤️ Like", callback_data=f"fd_like_{post['id']}_{offset}_{mode}"))
        if offset + 1 < total_posts:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"fd_pg_{mode}_{offset+1}"))
            
        action_row = [
            InlineKeyboardButton("✉️ DM Author", callback_data=f"fd_dm_{post['user_id']}"),
            InlineKeyboardButton("✍️ Create Post", callback_data="fd_create")
        ]
        rows = [cat_row, nav_row, action_row]
        
        # Author sees a delete button; everyone else sees a report button
        if post['user_id'] == viewer_id:
            rows.append([InlineKeyboardButton("🗑 Delete My Post", callback_data=f"fd_sdel_{post['id']}_{offset}_{mode}")])
        else:
            rows.append([InlineKeyboardButton("🚩 Report Post", callback_data=f"fd_rep_{post['id']}_{offset}_{mode}")])

        markup = InlineKeyboardMarkup(rows)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")

# --- FEED CALLBACKS ---
async def feed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    
    if data.startswith("fd_cat_"):
        mode = data.split('_')[2]
        await query.answer(f"Sorting by {mode}...")
        await send_feed_page(update, context, offset=0, mode=mode)
        
    elif data.startswith("fd_pg_"): # fd_pg_{mode}_{offset}
        parts = data.split('_')
        mode = parts[2]
        offset = int(parts[3])
        await query.answer()
        await send_feed_page(update, context, offset, mode=mode)
        
    elif data.startswith("fd_like_"): # fd_like_{post_id}_{offset}_{mode}
        parts = data.split('_')
        post_id = int(parts[2])
        offset = int(parts[3])
        mode = parts[4] if len(parts) > 4 else 'trending'
        
        if db.like_wall_post(post_id, user_id):
            await query.answer("❤️ You liked this post!")
            await send_feed_page(update, context, offset, mode=mode)
        else:
            await query.answer("❌ You already liked this post.", show_alert=True)
            
    elif data.startswith("fd_sdel_"): # fd_sdel_{post_id}_{offset}_{mode}
        parts = data.split('_')
        post_id = int(parts[2])
        offset = int(parts[3])
        mode = parts[4] if len(parts) > 4 else 'trending'
        
        # Verify ownership
        post = db.get_wall_post_by_id(post_id)
        if post and post['user_id'] == user_id:
            db.delete_wall_post(post_id)
            await query.answer("🗑 Your post has been deleted.", show_alert=False)
            # Reload feed
            await send_feed_page(update, context, max(0, offset - 1) if offset > 0 else 0, mode=mode)
        else:
            await query.answer("❌ You don't own this post.", show_alert=True)
            
    elif data.startswith("fd_rep_"): # fd_rep_{post_id}_{offset}_{mode}
        parts = data.split('_')
        post_id = int(parts[2])
        offset = int(parts[3])
        mode = parts[4] if len(parts) > 4 else 'trending'

        status, count = db.report_wall_post(user_id, post_id)

        if status == 'already_reported':
            await query.answer("❌ You have already reported this post.", show_alert=True)

        elif status == 'auto_deleted':
            await query.answer("🚩 Post removed! It was reported too many times.", show_alert=True)
            # Refresh feed
            await send_feed_page(update, context, max(0, offset - 1), mode=mode)

        else:  # 'reported'
            remaining = 3 - count
            await query.answer(
                f"🚩 Reported! ({count}/3 reports) — {remaining} more needed to auto-remove.",
                show_alert=True
            )
            await send_feed_page(update, context, offset, mode=mode)
        
    elif data.startswith("fd_dm_"):
        author_id = int(data.split('_')[2])
        
        if author_id == user_id:
            await query.answer("❌ You can't DM yourself!", show_alert=True)
            return
            
        if db.get_active_chat(user_id):
            await query.answer("❌ Stop your current chat first before sending a DM request.", show_alert=True)
            return
            
        if db.get_active_chat(author_id):
            await query.answer("😔 The author is currently in another chat. Try again later.", show_alert=True)
            return
            
        await query.answer()
        
        # Send a request to the author — do NOT connect instantly
        try:
            req_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Accept", callback_data=f"fdreq_acc_{user_id}"),
                 InlineKeyboardButton("❌ Decline", callback_data=f"fdreq_dec_{user_id}")]
            ])
            await context.bot.send_message(
                chat_id=author_id,
                text="📩 *DM Request from the Global Feed*\n\nSomeone read your post and wants to connect with you anonymously!",
                reply_markup=req_markup,
                parse_mode="Markdown"
            )
            await query.edit_message_text(
                "⏳ *Request Sent!*\n\nWaiting for the author to accept your DM request...",
                parse_mode="Markdown"
            )
        except Exception:
            await query.edit_message_text("❌ Could not reach the author. They may have blocked the bot.")
            
    elif data == "fd_create":
        # Check balance
        user = db.get_user(user_id)
        if user and user.get('coins', 0) >= 25:
            await query.answer()
            await query.edit_message_text("✍️ *Create an Anonymous Post*\n\nType what's on your mind (Max 200 characters).\nThis will cost 25 Coins.\n\nType /cancel to abort.", parse_mode="Markdown")
            return FEED_POST_INPUT
        else:
            await query.answer("❌ You need at least 25 Coins to make a post. Try using /daily or referring a friend!", show_alert=True)
            return ConversationHandler.END

# --- POST CREATION FLOW ---
async def feed_post_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if len(text) > 200:
        await update.message.reply_text("❌ Your post is too long! Keep it under 200 characters.\n\nTry again:")
        return FEED_POST_INPUT
        
    # Security/Sanitation (Simple replacement)
    clean_text = text.replace("<", "").replace(">", "").strip()
    
    # Check balance one last time
    user = db.get_user(user_id)
    if user and user.get('coins', 0) >= 25:
        db.add_coins(user_id, -25)
        db.add_wall_post(user_id, clean_text)
        await update.message.reply_text("✅ *Post successfully injected into the Global Feed!*", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Insufficient coins.")
        
    return ConversationHandler.END

async def cancel_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Post creation cancelled.", reply_markup=__import__('handlers.commands', fromlist=['get_main_keyboard']).get_main_keyboard())
    return ConversationHandler.END

async def feed_dm_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles Accept/Decline from the author side of a Feed DM request."""
    query = update.callback_query
    author_id = update.effective_user.id  # the post author receiving the request
    parts = query.data.split('_')
    action = parts[1]         # 'acc' or 'dec'
    requester_id = int(parts[2])  # the user who clicked DM Author

    await query.answer()

    if action == 'dec':
        await query.edit_message_text("❌ You declined the DM request.")
        try:
            await context.bot.send_message(
                chat_id=requester_id,
                text="😔 *The author declined your DM request.*",
                parse_mode="Markdown"
            )
        except:
            pass
        return

    # Action == 'acc' — do the actual connection now
    from handlers.commands import get_chat_keyboard
    
    # Safety checks at accept time too
    if db.get_active_chat(author_id):
        await query.edit_message_text("❌ You are already in a chat. Request cancelled.")
        try:
            await context.bot.send_message(chat_id=requester_id, text="😔 The author is now busy in another chat.")
        except:
            pass
        return

    if db.get_active_chat(requester_id):
        await query.edit_message_text("❌ The requester is now busy. Request cancelled.")
        return

    db.remove_from_queue(author_id)
    db.remove_from_queue(requester_id)
    db.create_chat(author_id, requester_id)

    # Notify author
    await query.edit_message_text(
        "🎉 *Connected!* You accepted the DM from the Global Feed. Say hi!",
        reply_markup=get_chat_keyboard(),
        parse_mode="Markdown"
    )

    # Notify requester
    try:
        await context.bot.send_message(
            chat_id=requester_id,
            text="🎉 *The author accepted your request!* You are now anonymously connected.",
            reply_markup=get_chat_keyboard(),
            parse_mode="Markdown"
        )
    except:
        pass
