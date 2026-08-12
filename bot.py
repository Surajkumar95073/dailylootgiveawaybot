import os
import random
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

PRIZE = "₹100"
WINNERS_COUNT = 4

# Giveaway data
participants = set()
giveaway_active = False


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 DAILY LOOT GIVEAWAY BOT 🎁\n\n"
        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"
        "Giveaway start karne ke liye /giveaway bhejo."
    )


# =========================
# /giveaway
# =========================

async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants, giveaway_active

    participants.clear()
    giveaway_active = True

    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 JOIN GIVEAWAY",
                callback_data="join"
            )
        ]
    ]

    await update.message.reply_text(
        "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"
        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"
        "👇 Giveaway join karne ke liye button dabao.\n\n"
        "👥 Participants: 0",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# JOIN BUTTON
# =========================

async def join_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    user = query.from_user

    if not giveaway_active:
        await query.answer(
            "❌ Giveaway active nahi hai.",
            show_alert=True
        )
        return

    if user.id in participants:
        await query.answer(
            "ℹ️ Aap already giveaway me joined ho!",
            show_alert=True
        )
        return

    participants.add(user.id)

    await query.answer(
        "✅ Giveaway me successfully join ho gaye!",
        show_alert=True
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 JOIN GIVEAWAY",
                callback_data="join"
            )
        ]
    ]

    try:
        await query.edit_message_text(
            "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"
            f"💰 Prize: {PRIZE}\n"
            f"🏆 Winners: {WINNERS_COUNT}\n\n"
            "👇 Giveaway join karne ke liye button dabao.\n\n"
            f"👥 Participants: {len(participants)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as error:
        logger.error(
            "Message update error: %s",
            error
        )


# =========================
# /end
# =========================

async def end_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global giveaway_active

    if not giveaway_active:
        await update.message.reply_text(
            "❌ Koi active giveaway nahi hai."
        )
        return

    if len(participants) < WINNERS_COUNT:
        await update.message.reply_text(
            "❌ Giveaway end nahi ho sakta.\n\n"
            f"👥 Participants: {len(participants)}\n"
            f"🏆 Required: {WINNERS_COUNT}\n\n"
            f"Kam se kam {WINNERS_COUNT} participants chahiye."
        )
        return

    giveaway_active = False

    winners = random.sample(
        list(participants),
        WINNERS_COUNT
    )

    message = (
        "🎉🎉 DAILY LOOT GIVEAWAY WINNERS 🎉🎉\n\n"
        f"💰 Prize: {PRIZE}\n\n"
    )

    for number, user_id in enumerate(winners, start=1):

        try:
            user = await context.bot.get_chat(user_id)

            if user.username:
                winner_name = f"@{user.username}"
            else:
                winner_name = user.first_name or "Winner"

            message += (
                f"🏆 Winner {number}: {winner_name}\n"
            )

        except Exception:
            message += (
                f"🏆 Winner {number}: User {user_id}\n"
            )

    message += (
        "\n🎁 Congratulations to all winners! 🎁\n"
        "\n❤️ Daily Loot Giveaway"
    )

    await update.message.reply_text(message)


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.error(
        "Bot error: %s",
        context.error
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN GitHub Secret me nahi mila."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("giveaway", giveaway)
    )

    application.add_handler(
        CommandHandler("end", end_giveaway)
    )

    application.add_handler(
        CallbackQueryHandler(
            join_giveaway,
            pattern="^join$"
        )
    )

    application.add_error_handler(
        error_handler
    )

    print(
        "🤖 Daily Loot Giveaway Bot is running..."
    )

    application.run_polling(
        drop_pending_updates=True
    )


# =========================
# START BOT
# =========================

if __name__ == "__main__":
    main()
