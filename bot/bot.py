import os
from django.conf import settings
from django.urls import reverse
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    InlineQueryHandler,
)
from telegram import InlineQueryResultGame, Update

from urllib.parse import quote_plus

from tetris.models import TetrisScore

TETRIS_GAME_SHORT_NAME = "tetris"  # set this in BotFather as the Game short name




def build_game_url(user_id: int, chat_id: int, username: str | None = "") -> str:
    base = settings.SITE_URL.rstrip("/")
    path = reverse("tetris:play")
    username = username or ""
    return (
        f"{base}{path}"
        f"?user_id={user_id}"
        f"&chat_id={chat_id}"
        f"&username={quote_plus(username)}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎮 Welcome to *Hirbots Game Hub*!\n\n"
        "First game: *Tetris*.\n"
        "Use /tetris to start playing.\n\n"
        "Leaderboards:\n"
        "• /top_global – global top players\n"
        "• /top_group – this chat’s top players"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def tetris_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends Telegram Game message. User taps 'Play' -> callback_query with game_short_name.
    """
    chat_id = update.effective_chat.id
    await context.bot.send_game(
        chat_id=chat_id,
        game_short_name=TETRIS_GAME_SHORT_NAME,
    )


from telegram import Update
from telegram.ext import ContextTypes

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.game_short_name != TETRIS_GAME_SHORT_NAME:
        await query.answer(text="Unknown game.", show_alert=True)
        return

    user = query.from_user

    # If message exists (normal chat), use that chat id.
    # If not (inline-only), fall back to user.id as a "chat" bucket.
    if query.message:
        chat_id = query.message.chat.id
    else:
        # inline_message only – no chat object
        chat_id = user.id

    url = build_game_url(
        user_id=user.id,
        chat_id=chat_id,
        username=user.username,
    )

    # Answer ONCE with URL so Telegram opens the webview
    await query.answer(url=url)

    
def format_scores(scores, limit=10):
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for idx, s in enumerate(scores[:limit], start=1):
        label = medals[idx - 1] if idx <= 3 else f"{idx}."
        name = s.username or str(s.user_id)
        lines.append(f"{label} {name} — *{s.best_score}*")
    if not lines:
        return "No scores yet. Be the first to play! 🎮"
    return "\n".join(lines)


async def top_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = TetrisScore.objects.order_by("-best_score", "-updated_at")[:10]
    text = "*🌍 Global Tetris Leaderboard*\n\n" + format_scores(list(scores))
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def top_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    scores = (
        TetrisScore.objects.filter(chat_id=chat_id)
        .order_by("-best_score", "-updated_at")[:10]
    )
    text = "*👥 Group Tetris Leaderboard*\n\n" + format_scores(list(scores))
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query

    # Simple: always return the Tetris game
    results = [
        InlineQueryResultGame(
            id="tetris_1",
            game_short_name=TETRIS_GAME_SHORT_NAME,
        )
    ]
    await query.answer(results=results, cache_time=0)

def build_application() -> Application:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tetris", tetris_command))
    app.add_handler(CommandHandler("top_global", top_global))
    app.add_handler(CommandHandler("top_group", top_group))

    # inline games
    app.add_handler(InlineQueryHandler(inline_query))

    # game "Play" button callback
    app.add_handler(CallbackQueryHandler(game_callback))

    return app
