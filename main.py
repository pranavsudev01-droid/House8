import os
import logging
from datetime import datetime, timezone
from typing import Any

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# House8 Telegram Bot — safe, read-only starter.
# It does NOT log in to Quotex or place trades.
# A compatible candle-data API must be configured before /signal can work.

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CANDLE_API_URL = os.getenv("CANDLE_API_URL", "").strip()
CANDLE_API_KEY = os.getenv("CANDLE_API_KEY", "").strip()

ASSETS = {
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "EURUSD_OTC": "EUR/USD OTC",
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("house8")


def fetch_candles(symbol: str, timeframe: str) -> list[dict[str, Any]]:
    """Fetch candles from a user-configured API.

    Expected response:
    {
      "candles": [
        {"time": "2026-11-11T10:00:00Z",
         "open": 1.10, "high": 1.11, "low": 1.09, "close": 1.105}
      ]
    }
    The API must return at least 60 completed candles, oldest first.
    """
    if not CANDLE_API_URL:
        raise RuntimeError(
            "Live candle feed is not configured. Set CANDLE_API_URL first."
        )

    headers = {"Accept": "application/json"}
    if CANDLE_API_KEY:
        headers["Authorization"] = f"Bearer {CANDLE_API_KEY}"

    response = requests.get(
        CANDLE_API_URL,
        params={"symbol": symbol, "timeframe": timeframe, "limit": 100},
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    candles = payload.get("candles") if isinstance(payload, dict) else None

    if not isinstance(candles, list) or len(candles) < 60:
        raise RuntimeError("Feed must return at least 60 candles.")

    clean = []
    for candle in candles:
        clean.append({
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"]),
        })
    return clean


def ichimoku_signal(candles: list[dict[str, float]]) -> tuple[str, str]:
    """Basic Ichimoku direction check using completed candles.

    Tenkan: 9 periods; Kijun: 26; Senkou B: 52.
    This is a simple screening rule, not a guarantee or a full trading system.
    """
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    def midpoint(period: int, end: int) -> float:
        start = end - period + 1
        return (max(highs[start:end + 1]) + min(lows[start:end + 1])) / 2

    i = len(candles) - 1
    tenkan = midpoint(9, i)
    kijun = midpoint(26, i)
    span_a_now = (tenkan + kijun) / 2
    span_b_now = midpoint(52, i)
    price = closes[i]
    cloud_top = max(span_a_now, span_b_now)
    cloud_bottom = min(span_a_now, span_b_now)

    if price > cloud_top and tenkan > kijun:
        return "CALL", "Price is above the cloud and Tenkan is above Kijun."
    if price < cloud_bottom and tenkan < kijun:
        return "PUT", "Price is below the cloud and Tenkan is below Kijun."
    return "WAIT", "Price is inside/near the cloud or trend confirmation is mixed."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🏠 HOUSE8 TRADING BOT\n\n"
        "Welcome! The bot is online.\n\n"
        "Commands:\n"
        "/start — Welcome message\n"
        "/status — Bot and feed status\n"
        "/help — Help\n"
        "/assets — Supported starter symbols\n"
        "/signal EURUSD M1 — Check an Ichimoku setup\n\n"
        "Markets: EUR/USD, GBP/USD, USD/JPY, EUR/USD OTC\n"
        "Timeframes: M1 and M5\n\n"
        "⚠️ Signals are informational only. No trades are placed."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "HOUSE8 HELP\n\n"
        "/status\n"
        "/assets\n"
        "/signal EURUSD M1\n"
        "/signal GBPUSD M5\n\n"
        "Use one of the symbols shown by /assets.\n"
        "A live candle-data API must be configured before signals are available."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    feed_status = "configured" if CANDLE_API_URL else "not configured"
    await update.message.reply_text(
        "🟢 HOUSE8 BOT STATUS\n\n"
        "Telegram bot: Online\n"
        f"Live candle feed: {feed_status}\n"
        "Signal engine: Ichimoku screening enabled\n"
        "Trade execution: Disabled"
    )


async def assets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["📊 HOUSE8 STARTER ASSETS"]
    lines.extend(f"• {code} — {name}" for code, name in ASSETS.items())
    lines.append("\nTimeframes: M1, M5")
    await update.message.reply_text("\n".join(lines))


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /signal EURUSD M1\n"
            "Example: /signal GBPUSD M5"
        )
        return

    symbol = context.args[0].upper()
    timeframe = context.args[1].upper()

    if symbol not in ASSETS:
        await update.message.reply_text("Unknown symbol. Use /assets.")
        return
    if timeframe not in {"M1", "M5"}:
        await update.message.reply_text("Timeframe must be M1 or M5.")
        return

    try:
        candles = fetch_candles(symbol, timeframe)
        direction, reason = ichimoku_signal(candles)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        await update.message.reply_text(
            f"🏠 HOUSE8 ICHIMOKU CHECK\n\n"
            f"Asset: {ASSETS[symbol]}\n"
            f"Timeframe: {timeframe}\n"
            f"Result: {direction}\n"
            f"Reason: {reason}\n"
            f"Checked: {now}\n\n"
            "⚠️ Educational signal only. Confirm on your chart; "
            "this is not financial advice."
        )
    except requests.RequestException as exc:
        logger.exception("Candle feed request failed")
        await update.message.reply_text(
            "The candle-data service could not be reached. "
            "Check the feed URL/API key and try again."
        )
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        logger.warning("Signal unavailable: %s", exc)
        await update.message.reply_text(f"Signal unavailable: {exc}")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing. Add it as a repository secret."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("assets", assets))
    app.add_handler(CommandHandler("signal", signal))

    logger.info("House8 Telegram bot is starting...")
    # run_polling manages initialization and shutdown itself.
    app.run_polling()


if __name__ == "__main__":
    main()
