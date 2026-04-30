import logging
import os
import sys
import time
import requests
import threading
from telegram.ext import Application
from config import BOT_TOKEN
from handlers import setup_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def on_startup(application):
    """Notify admins when the bot comes online."""
    from config import ADMIN_IDS
    
    print(f"Bot is online! Notifying {len(ADMIN_IDS)} admins...")
    
    for aid in ADMIN_IDS:
        try:
            await application.bot.send_message(
                chat_id=aid,
                text="🛡️ *Admin Notification*\n\nThe bot is now back online and ready.",
                parse_mode="Markdown"
            )
        except Exception:
            continue
            
    print("Admin startup notification complete.")

def run_bot():
    application = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()

    # Register handlers
    setup_handlers(application)

    # Start the Bot
    application.run_polling()


def delete_webhook():
    print("Checking for active webhooks...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("ok"):
            print("Webhook successfully cleared.")
        else:
            print(f"Info: {data.get('description', 'No active webhook found.')}")
    except Exception as e:
        print(f"Warning: Could not delete webhook: {e}")

def run_web_admin():
    try:
        from web_admin.app import app
        port = int(os.environ.get("PORT", 5000))
        print(f"Starting Web Admin Panel on port {port}...")
        # Bind to 0.0.0.0 and the PORT environment variable for Render compatibility
        app.run(host="0.0.0.0", port=port, use_reloader=False, debug=False)
    except Exception as e:
        print(f"Failed to start web admin: {e}")

def main():
    if "--bot-only" in sys.argv:
        delete_webhook()
        run_bot()
        return

    # Clear webhook to ensure polling works on Render
    delete_webhook()
    
    # Start the web server in a background thread.
    # This ensures both the bot and web admin share the same process,
    # fitting within Render's memory limits and satisfying the port binding requirement.
    web_thread = threading.Thread(target=run_web_admin, daemon=True)
    web_thread.start()

    time.sleep(1)  # Give it a brief moment to start

    print("Starting Telegram Bot...")
    try:
        # Run bot in the main thread (this is a blocking call)
        run_bot()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")

if __name__ == "__main__":
    main()
