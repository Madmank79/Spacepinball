#!/usr/bin/env python3
"""
Cosmic Flipper – Space Pinball for Telegram
A simple but addictive text-based pinball game set in deep space.
"""

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
TOKEN = "8843510657:AAGzWuoFgxxMcDsr-DKhHLqA1ZX8nZpa37Y"          # ← put your bot token here
ADMIN_ID = None                        # optional: your Telegram user ID

# Game constants
TABLE_WIDTH = 11
TABLE_HEIGHT = 14
START_LIVES = 3
FLIPPER_COOLDOWN = 1.2                 # seconds between flips (anti-spam)

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# GAME STATE (per chat)
# ──────────────────────────────────────────────
games = {}   # chat_id → game dict

def new_game():
    return {
        "ball_x": TABLE_WIDTH // 2,
        "ball_y": 2,
        "vx": random.choice([-1, 1]),
        "vy": 1,
        "score": 0,
        "lives": START_LIVES,
        "combo": 0,
        "last_flip": 0,
        "running": True,
        "message_id": None,
    }

# ──────────────────────────────────────────────
# RENDER THE TABLE
# ──────────────────────────────────────────────
def render_table(g):
    # Empty space grid
    grid = [["·" for _ in range(TABLE_WIDTH)] for _ in range(TABLE_HEIGHT)]

    # Top wall (stars)
    for x in range(TABLE_WIDTH):
        grid[0][x] = "✦"

    # Side walls
    for y in range(TABLE_HEIGHT):
        grid[y][0] = "│"
        grid[y][TABLE_WIDTH - 1] = "│"

    # Bottom drain zone
    for x in range(1, TABLE_WIDTH - 1):
        grid[TABLE_HEIGHT - 1][x] = "═"

    # Bumpers (planets)
    bumpers = [
        (3, 4, "🪐"),   # Jupiter
        (7, 3, "🌕"),   # Moon
        (5, 7, "⚫"),   # Black hole (dangerous)
        (2, 9, "🌍"),   # Earth
        (8, 8, "🔴"),   # Mars
    ]
    for bx, by, symbol in bumpers:
        if 0 <= by < TABLE_HEIGHT and 0 <= bx < TABLE_WIDTH:
            grid[by][bx] = symbol

    # Flippers (force fields)
    # Left flipper
    grid[TABLE_HEIGHT - 3][2] = "⟸"
    grid[TABLE_HEIGHT - 3][3] = "⟸"
    # Right flipper
    grid[TABLE_HEIGHT - 3][TABLE_WIDTH - 4] = "⟹"
    grid[TABLE_HEIGHT - 3][TABLE_WIDTH - 3] = "⟹"

    # Ball
    bx, by = g["ball_x"], g["ball_y"]
    if 0 <= by < TABLE_HEIGHT and 0 <= bx < TABLE_WIDTH:
        grid[by][bx] = "☄️"

    # Build the message
    lines = [
        "🌌  **COSMIC FLIPPER**  🌌",
        f"Score: `{g['score']}`   Lives: {'❤️' * g['lives']}   Combo: x{g['combo']}",
        "─────────────────────",
    ]
    for row in grid:
        lines.append("".join(row))
    lines.append("─────────────────────")
    lines.append("Use the force fields to keep the asteroid in play!")
    return "\n".join(lines)

# ──────────────────────────────────────────────
# PHYSICS STEP
# ──────────────────────────────────────────────
def step(g):
    if not g["running"]:
        return

    # Move
    g["ball_x"] += g["vx"]
    g["ball_y"] += g["vy"]

    # Bounce off side walls
    if g["ball_x"] <= 1 or g["ball_x"] >= TABLE_WIDTH - 2:
        g["vx"] *= -1
        g["ball_x"] = max(1, min(TABLE_WIDTH - 2, g["ball_x"]))

    # Bounce off top
    if g["ball_y"] <= 1:
        g["vy"] = abs(g["vy"])
        g["ball_y"] = 1

    # Drain (bottom)
    if g["ball_y"] >= TABLE_HEIGHT - 1:
        g["lives"] -= 1
        g["combo"] = 0
        if g["lives"] <= 0:
            g["running"] = False
            return
        # Reset ball
        g["ball_x"] = TABLE_WIDTH // 2
        g["ball_y"] = 2
        g["vx"] = random.choice([-1, 1])
        g["vy"] = 1
        return

    # Bumper collisions
    bumpers = {(3, 4), (7, 3), (5, 7), (2, 9), (8, 8)}
    pos = (g["ball_x"], g["ball_y"])
    if pos in bumpers:
        g["vx"] *= -1
        g["vy"] *= -1
        # Black hole is mean
        if pos == (5, 7):
            g["score"] += 50
            g["combo"] += 2
        else:
            g["score"] += 25
            g["combo"] += 1
        g["score"] += g["combo"] * 5

    # Flipper collision zone (very simple)
    if g["ball_y"] == TABLE_HEIGHT - 3:
        if 2 <= g["ball_x"] <= 3 or TABLE_WIDTH - 4 <= g["ball_x"] <= TABLE_WIDTH - 3:
            g["vy"] = -abs(g["vy"])
            g["score"] += 10
            g["combo"] += 1

# ──────────────────────────────────────────────
# KEYBOARD
# ──────────────────────────────────────────────
def get_keyboard(running: bool):
    if not running:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Play Again", callback_data="restart")]
        ])
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⟸ LEFT FORCE", callback_data="left"),
            InlineKeyboardButton("RIGHT FORCE ⟹", callback_data="right"),
        ],
        [InlineKeyboardButton("⏸ Pause / Status", callback_data="status")]
    ])

# ──────────────────────────────────────────────
# HANDLERS
# ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games[chat_id] = new_game()
    g = games[chat_id]

    text = render_table(g)
    msg = await update.message.reply_text(
        text,
        reply_markup=get_keyboard(True),
        parse_mode="Markdown"
    )
    g["message_id"] = msg.message_id

    # Start the game loop
    context.job_queue.run_repeating(
        game_tick,
        interval=0.7,
        first=0.7,
        chat_id=chat_id,
        name=str(chat_id)
    )

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
            f"{'🏆 ORBIT MASTER!' if g['score'] >= 500 else 'Try again, pilot.'}"
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
        # Cancel old job
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()

        games[chat_id] = new_game()
        g = games[chat_id]
        text = render_table(g)
        await query.edit_message_text(
            text,
            reply_markup=get_keyboard(True),
            parse_mode="Markdown"
        )
        g["message_id"] = query.message.message_id

        context.job_queue.run_repeating(
            game_tick,
            interval=0.7,
            first=0.7,
            chat_id=chat_id,
            name=str(chat_id)
        )
        return

    if not g["running"]:
        return

    # Simple flipper action – reverse vertical direction if ball is near bottom
    if data in ("left", "right"):
        if g["ball_y"] >= TABLE_HEIGHT - 5:
            g["vy"] = -abs(g["vy"])
            # Give a little horizontal push
            if data == "left":
                g["vx"] = -1
            else:
                g["vx"] = 1
            g["score"] += 5

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌌 **Cosmic Flipper**\n\n"
        "Keep the runaway asteroid (☄️) from falling into the void!\n"
        "Use the magnetic force fields (⟸ ⟹) to bounce it back up.\n"
        "Hit planets for points. Avoid losing all your lives.\n\n"
        "Commands:\n"
        "/start – Launch a new game\n"
        "/help  – This message",
        parse_mode="Markdown"
    )

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))

    print("🚀 Cosmic Flipper is online...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
