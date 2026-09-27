#!/usr/bin/env python3
"""
Cosmic Flipper – Launches the real arcade pinball game
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# ──────────────────────────────────────────────
# PUT YOUR BOT TOKEN HERE
# ──────────────────────────────────────────────
TOKEN = "8843510657:AAGzWuoFgxxMcDsr-DKhHLqA1ZX8nZpa37Y"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This opens the real arcade game
    await update.message.reply_game("Pinball")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌌 Cosmic Flipper\n\n"
        "Send /start to play the arcade pinball game!"
    )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    print("🚀 Cosmic Flipper (Arcade) is online...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
