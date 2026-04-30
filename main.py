import logging
import os
import subprocess
import sys
import time

import requests
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


def main():
    if "--bot-only" in sys.argv:
        run_bot()
        return

    delete_webhook()
    print("Starting Telegram Bot...")
    bot_process = subprocess.Popen([sys.executable, "main.py", "--bot-only"])

    time.sleep(1)  # Give it a brief moment to start

    web_port = os.getenv("PORT", "5000")
    print(f"Starting Web Admin Panel on http://0.0.0.0:{web_port} ...")
    admin_process = subprocess.Popen([sys.executable, "web_admin/app.py"])

    print("\nBoth processes are running! Press Ctrl+C to stop both safely.\n")

    try:
        # Keep running until one crashes or user presses Ctrl+C
        while True:
            time.sleep(1)
            if bot_process.poll() is not None:
                print("\nTelegram Bot stopped unexpectedly.")
                break
            if admin_process.poll() is not None:
                print("\nWeb Admin Panel stopped unexpectedly.")
                break

    except KeyboardInterrupt:
        print("\nShutting down processes...")

    # Gracefully terminate both
    bot_process.terminate()
    admin_process.terminate()
    bot_process.wait()
    admin_process.wait()
    print("All processes completely terminated.")

if __name__ == "__main__":
    main()
