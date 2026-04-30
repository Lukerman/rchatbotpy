from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from .commands import setup_command_handlers
from .chat import setup_chat_handler
from .settings import settings_callback
from .economy import shop_callback, promo_command, promo_input, cancel_promo, PROMO_INPUT
from .profile import edit_profile_start, profile_gender, profile_age_text, profile_age_skip, profile_location_start, profile_location_received, profile_location_skip, profile_interests_text, profile_interests_skip, cancel_profile, GENDER, AGE, LOCATION, INTERESTS
from .post_chat import (
    rate_callback, reconnect_callback, reconnect_action_callback, 
    block_callback, report_callback, report_submit_callback,
    block_command, report_command, gift_command, gift_callback, media_action_callback,
    media_report_callback
)
from .admin import (
    admin_command, admin_callback, admin_broadcast_msg, 
    admin_ban_user, admin_unban_user, admin_coins_user, admin_coins_amt, cancel_admin,
    admin_user_lookup, admin_user_action, admin_config_callback, admin_promo_callback,
    admin_promo_input_code, admin_promo_input_amt, admin_promo_input_uses,
    BROADCAST_MSG, BAN_USER, UNBAN_USER, COINS_USER, COINS_AMT,
    USER_LOOKUP, CONFIG_MESS, PROMO_CODE, PROMO_AMT, PROMO_LIMIT
)
from .feed import feed_callback, feed_post_input, cancel_feed, FEED_POST_INPUT, feed_dm_action_callback
from .membership import subscription_check_handler, check_sub_callback
from .maintenance import chat_cleanup_job

def setup_handlers(application):
    application.add_handler(MessageHandler(filters.ALL, subscription_check_handler), group=-1)
    application.add_handler(CallbackQueryHandler(subscription_check_handler), group=-1)
    
    # Maintenance Mode Check (Group -2 runs before regular but after forced sub)
    from .maintenance import maintenance_check
    application.add_handler(MessageHandler(filters.ALL, maintenance_check), group=-2)
    application.add_handler(CallbackQueryHandler(maintenance_check), group=-2)
    
    # Registered periodic maintenance jobs
    if application.job_queue:
        from .maintenance import chat_cleanup_job, scheduled_broadcast_job
        application.job_queue.run_repeating(chat_cleanup_job, interval=30, first=10)
        application.job_queue.run_repeating(scheduled_broadcast_job, interval=60, first=20)

    # Admin root command
    application.add_handler(CommandHandler('admin', admin_command))
    
    # Admin Panel Conversation
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^adm_")],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_msg)],
            BAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_user)],
            UNBAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_unban_user)],
            COINS_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_coins_user)],
            COINS_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_coins_amt)],
            USER_LOOKUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_user_lookup)],
            CONFIG_MESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_config_callback)],
            PROMO_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_promo_input_code)],
            PROMO_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_promo_input_amt), CallbackQueryHandler(admin_promo_input_amt, pattern="^admpr_type_")],
            PROMO_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_promo_input_uses)]
        },
        fallbacks=[CommandHandler('cancel', cancel_admin), CallbackQueryHandler(admin_callback, pattern="^adm_")],
        per_message=False
    )
    application.add_handler(admin_conv)
    
    # Admin Action Callbacks (Sub-menus)
    application.add_handler(CallbackQueryHandler(admin_user_action, pattern="^admusr_"))
    application.add_handler(CallbackQueryHandler(admin_config_callback, pattern="^admcfg_"))
    application.add_handler(CallbackQueryHandler(admin_promo_callback, pattern="^admpr_"))
    feed_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(feed_callback, pattern="^fd_")],
        states={
            FEED_POST_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, feed_post_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel_feed), MessageHandler(filters.Regex('^🛑 Stop Chat$'), cancel_feed)],
        per_message=False
    )
    application.add_handler(feed_conv)
    application.add_handler(CallbackQueryHandler(feed_dm_action_callback, pattern="^fdreq_"))

    # Post-chat & Moderation Callbacks
    application.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate_"))
    application.add_handler(CallbackQueryHandler(reconnect_callback, pattern=r"^reconnect_\d+$"))
    application.add_handler(CallbackQueryHandler(reconnect_action_callback, pattern="^reconnect_(accept|decline)_"))
    application.add_handler(CallbackQueryHandler(block_callback, pattern="^block_"))
    application.add_handler(CallbackQueryHandler(report_callback, pattern="^report_"))
    application.add_handler(CallbackQueryHandler(report_submit_callback, pattern="^rptsbmt_"))
    application.add_handler(CallbackQueryHandler(gift_callback, pattern="^gift_"))
    application.add_handler(CallbackQueryHandler(media_action_callback, pattern="^med(acc|dec)_"))
    application.add_handler(CallbackQueryHandler(media_report_callback, pattern="^medrep_"))
    
    # Settings / Shop Callbacks
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^(setpref_|shop_vip)"))
    application.add_handler(CallbackQueryHandler(shop_callback, pattern="^buy_vip_"))
    
    # Profile Conversation
    prof_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_profile_start, pattern="^edit_profile$")],
        states={
            GENDER: [CallbackQueryHandler(profile_gender, pattern="^prof_")],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_age_text), CallbackQueryHandler(profile_age_skip, pattern="^prof_skip$")],
            LOCATION: [CallbackQueryHandler(profile_location_start, pattern="^prof_loc_req$"), MessageHandler(filters.LOCATION, profile_location_received), CallbackQueryHandler(profile_location_skip, pattern="^prof_skip$")],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_interests_text), CallbackQueryHandler(profile_interests_skip, pattern="^prof_skip$")]
        },
        fallbacks=[CommandHandler('cancel', cancel_profile), MessageHandler(filters.Regex('^🛑 Stop Chat$'), cancel_profile)],
        per_message=False
    )
    application.add_handler(prof_conv_handler)
    
    # Promo Code Conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('promo', promo_command), MessageHandler(filters.Regex('^🎫 Promo Code$'), promo_command)],
        states={
            PROMO_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel_promo), MessageHandler(filters.Regex('^🛑 Stop Chat$'), cancel_promo)]
    )
    application.add_handler(conv_handler)
    
    # Text commands for block/report/gift inside chat
    application.add_handler(CommandHandler('block', block_command))
    application.add_handler(CommandHandler('report', report_command))
    application.add_handler(CommandHandler('gift', gift_command))

    setup_command_handlers(application)
    
    # Location Handlers
    from handlers.location import location_command, handle_location
    application.add_handler(CommandHandler('location', location_command))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    # Saved Chats Handlers
    from handlers.saved_chats import saved_chats_command, view_saved_callback
    from handlers.post_chat import save_chat_callback
    application.add_handler(CommandHandler('saved', saved_chats_command))
    application.add_handler(CallbackQueryHandler(saved_chats_command, pattern="^saved_list$"))
    application.add_handler(CallbackQueryHandler(view_saved_callback, pattern="^viewsaved_"))
    application.add_handler(CallbackQueryHandler(save_chat_callback, pattern="^savechat_"))
    
    # Settings callbacks (Add location setting check)
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^setreg_"))

    # Membership check callback
    application.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))

    setup_chat_handler(application)
