
import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# START COMMAND
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = """
🏠 HOUSE8 TRADING BOT

Welcome!

Your Ichimoku signal system is being prepared.

Available commands:

/start - Start the bot
/status - Check bot status
/help - Help and information

📊 Markets: OTC & Normal
📈 Strategy: Ichimoku
⏱ Timeframes: M1 & M5

⚠️ Signals are under development.
"""
    await update.message.reply_text(message)


# STATUS COMMAND
async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "🟢 HOUSE8 BOT STATUS\n\n"
        "Bot is online.\n"
        "Ichimoku signal system: Under development."
    )


# HELP COMMAND
async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "🏠 HOUSE8 HELP\n\n"
        "/start - Welcome message\n"
        "/status - System status\n"
        "/help - Help information"
    )


# MAIN FUNCTION
def main():

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing from GitHub Secrets."
        )

    application = (
        Application.builder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .get_updates_read_timeout(30)
        .build()
    )

    # Register commands
    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("status", status)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    logger.info("HOUSE8 BOT IS STARTING...")

    # Start Telegram bot
    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
