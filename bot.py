#!/usr/bin/env python3
"""
Cosmic Flipper – Space Pinball Telegram Bot
Plays completely inside Telegram (like Sonic Slots)
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ──────────────────────────────────────────────
# PUT YOUR BOT TOKEN HERE
# ──────────────────────────────────────────────
TOKEN = "8843510657:AAGzWuoFgxxMcDsr-DKhHLqA1ZX8nZpa37Y"

# Game settings
TABLE_WIDTH = 11
TABLE_HEIGHT = 13
START_LIVES = 3

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

games = {}

def new_game():
    return {
        "ball_x": TABLE_WIDTH // 2,
        "ball_y": 2,
        "vx": random.choice([-1, 1]),
        "vy": 1,
        "score": 0,
        "lives": START_LIVES,
        "combo": 0,
        "running": True,
        "message_id": None,
    }

def render_table(g):
    grid = [["·" for _ in range(TABLE_WIDTH)] for _ in range(TABLE_HEIGHT)]

    # Top wall
    for x in range(TABLE_WIDTH):
        grid[0][x] = "✦"

    # Side walls
    for y in range(TABLE_HEIGHT):
        grid[y][0] = "│"
        grid[y][TABLE_WIDTH-1] = "│"

    # Bottom
    for x in range(1, TABLE_WIDTH-1):
        grid[TABLE_HEIGHT-1][x] = "═"

    # Planets / bumpers
    bumpers = [
        (3, 3, "🪐"),
        (7, 2, "🌕"),
        (5, 6, "⚫"),
        (2, 8, "🌍"),
        (8, 7, "🔴"),
    ]
    for bx, by, symbol in bumpers:
        if 0 < by < TABLE_HEIGHT-1 and 0 < bx < TABLE_WIDTH-1:
            grid[by][bx] = symbol

    # Flippers
    grid[TABLE_HEIGHT-3][2] = "⟸"
    grid[TABLE_HEIGHT-3][3] = "⟸"
    grid[TABLE_HEIGHT-3][TABLE_WIDTH-4] = "⟹"
    grid[TABLE_HEIGHT-3][TABLE_WIDTH-3] = "⟹"

    # Ball
    bx, by = g["ball_x"], g["ball_y"]
    if 0 <= by < TABLE_HEIGHT and 0 <= bx < TABLE_WIDTH:
        grid[by][bx] = "☄️"

    lines = [
        "🌌 **COSMIC FLIPPER** 🌌",
        f"Score: `{g['score']}`   Lives: {'❤️' * g['lives']}   Combo: x{g['combo']}",
        "─────────────────────",
    ]
    for row in grid:
        lines.append("".join(row))
    lines.append("─────────────────────")
    lines.append("Keep the asteroid in play!")
    return "\n".join(lines)

def step(g):
    if not g["running"]:
        return

    g["ball_x"] += g["vx"]
    g["ball_y"] += g["vy"]

    # Side walls
    if g["ball_x"] <= 1 or g["ball_x"] >= TABLE_WIDTH-2:
        g["vx"] *= -1
        g["ball_x"] = max(1, min(TABLE_WIDTH-2, g["ball_x"]))

    # Top
    if g["ball_y"] <= 1:
        g["vy"] = abs(g["vy"])
        g["ball_y"] = 1

    # Drain
    if g["ball_y"] >= TABLE_HEIGHT-1:
        g["lives"] -= 1
        g["combo"] = 0
        if g["lives"] <= 0:
            g["running"] = False
            return
        g["ball_x"] = TABLE_WIDTH // 2
        g["ball_y"] = 2
        g["vx"] = random.choice([-1, 1])
        g["vy"] = 1
        return

    # Bumpers
    bumpers = {(3,3), (7,2), (5,6), (2,8), (8,7)}
    pos = (g["ball_x"], g["ball_y"])
    if pos in bumpers:
        g["vx"] *= -1
        g["vy"] *= -1
        if pos == (5,6):  # black hole
            g["score"] += 50
            g["combo"] += 2
        else:
            g["score"] += 25
            g["combo"] += 1
        g["score"] += g["combo"] * 5

    # Flipper zone
    if g["ball_y"] == TABLE_HEIGHT-3:
        if 2 <= g["ball_x"] <= 3 or TABLE_WIDTH-4 <= g["ball_x"] <= TABLE_WIDTH-3:
            g["vy"] = -abs(g["vy"])
            g["score"] += 10
            g["combo"] += 1

def get_keyboard(running: bool):
    if not running:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Play Again", callback_data="restart")]])
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⟸ LEFT", callback_data="left"),
            InlineKeyboardButton("RIGHT ⟹", callback_data="right"),
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games[chat_id] = new_game()
    g = games[chat_id]

    text = render_table(g)
    msg = await update.message.reply_text(text, reply_markup=get_keyboard(True), parse_mode="Markdown")
    g["message_id"] = msg.message_id

    context.job_queue.run_repeating(game_tick, interval=0.8, first=0.8, chat_id=chat_id, name=str(chat_id))

async def game_tick(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    if chat_id not in games:
        context.job.schedule_removal()
        return

    g = games[chat_id]
    if not g["running"]:
        context.job.schedule_removal()
        return

    step(g)
    text = render_table(g)

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=g["message_id"],
            text=text,
            reply_markup=get_keyboard(g["running"]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Edit failed: {e}")

    if not g["running"]:
        final = (
            f"💥 **ASTEROID LOST IN THE VOID** 💥\n\n"
            f"Final Score: `{g['score']}`\n"
            f"{'🏆 ORBIT MASTER!' if g['score'] >= 400 else 'Try again, pilot.'}"
        )
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=g["message_id"],
            text=final,
            reply_markup=get_keyboard(False),
            parse_mode="Markdown"
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if chat_id not in games:
        await query.edit_message_text("No active game. Type /start")
        return

    g = games[chat_id]

    if data == "restart":
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()

        games[chat_id] = new_game()
        g = games[chat_id]
        text = render_table(g)
        await query.edit_message_text(text, reply_markup=get_keyboard(True), parse_mode="Markdown")
        g["message_id"] = query.message.message_id

        context.job_queue.run_repeating(game_tick, interval=0.8, first=0.8, chat_id=chat_id, name=str(chat_id))
        return

    if not g["running"]:
        return

    if data in ("left", "right"):
        if g["ball_y"] >= TABLE_HEIGHT - 5:
            g["vy"] = -abs(g["vy"])
            g["vx"] = -1 if data == "left" else 1
            g["score"] += 5

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌌 **Cosmic Flipper**\n\n"
        "Keep the asteroid (☄️) from falling!\n"
        "Use the force field buttons to bounce it back up.\n"
        "Hit planets for points.\n\n"
        "/start – New game\n"
        "/help – This message",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    print("🚀 Cosmic Flipper bot is online...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
