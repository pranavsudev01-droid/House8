
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 HOUSE8\n\n"
        "Bot setup: Initial stage\n"
        "Signal engine: Not connected\n"
        "Market data: Not connected\n"
        "Tracking: Not connected"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "House8 Help\n\n"
        "/start - Welcome message\n"
        "/status - System status\n"
        "/help - Help"
    )

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("Telegram token is not configured")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))

    print("House8 is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
  
