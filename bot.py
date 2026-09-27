#!/usr/bin/env python3
"""
Cosmic Flipper – Launches the real arcade pinball game
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# ──────────────────────────────────────────────
# BOT TOKEN
# ──────────────────────────────────────────────
TOKEN = "8843510657:AAGzWuoFgxxMcDsr-DKhHLqA1ZX8nZpa37Y"

GAME_URL = "https://madmank79.github.io/Spacepinball/"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Use case 1: /start - Welcome message with play button"""
    keyboard = [
        [InlineKeyboardButton("🎮 Play Now", url=GAME_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌌 Welcome to Cosmic Flipper!\n\n"
        "This is an arcade pinball game. Tap the button below to play!",
        reply_markup=reply_markup
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Use case 2: /play - Launch the game directly"""
    keyboard = [
        [InlineKeyboardButton("🚀 Launch Game", url=GAME_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Ready to play? Tap the button to launch Cosmic Flipper!",
        reply_markup=reply_markup
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Use case 3: /help - Game instructions"""
    await update.message.reply_text(
        "🌌 Cosmic Flipper – How to Play\n\n"
        "🎮 Controls:\n"
        "• Left/Right arrows or A/D to flip\n"
        "• Space bar to launch the ball\n"
        "• On mobile: tap left/right to flip, tap center to launch\n\n"
        "⭐ Objective:\n"
        "• Hit bumpers to score points\n"
        "• Keep the ball in play with flippers\n"
        "• Don't lose all 3 lives!\n\n"
        "Use /play to start the game!"
    )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("help", help_cmd))

    print("🚀 Cosmic Flipper (Arcade) is online...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
