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

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = "@DailyLootGiveaway"
CHANNEL_LINK = "https://t.me/DailyLootGiveaway"

PRIZE = "₹100"
WINNERS_COUNT = 4

participants = set()
giveaway_active = False

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 DAILY LOOT GIVEAWAY BOT 🎁\n\n"
        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"
        "Giveaway start karne ke liye /giveaway bhejo."
    )


async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants, giveaway_active

    participants.clear()
    giveaway_active = True

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 JOIN CHANNEL",
                url=CHANNEL_LINK
            )
        ],
        [
            InlineKeyboardButton(
                "🎁 JOIN GIVEAWAY",
                callback_data="join"
            )
        ],
    ]

    await update.message.reply_text(
        "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"
        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"
        "1️⃣ पहले channel join करो\n"
        "2️⃣ फिर JOIN GIVEAWAY दबाओ\n\n"
        "👥 Participants: 0",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def join_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    user = query.from_user

    if not giveaway_active:
        await query.answer(
            "❌ Giveaway active नहीं है.",
            show_alert=True
        )
        return

    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user.id
        )

        if member.status in ["left", "kicked"]:
            await query.answer(
                "❌ पहले channel join करो!",
                show_alert=True
            )
            return

    except Exception as error:
        logger.error(
            "Membership check error: %s",
            error
        )

        await query.answer(
            "⚠️ Membership check नहीं हो पाया. "
            "थोड़ी देर बाद फिर try करो.",
            show_alert=True
        )
        return

    if user.id in participants:
        await query.answer(
            "ℹ️ आप पहले से giveaway में joined हो.",
            show_alert=True
        )
        return

    participants.add(user.id)

    await query.answer(
        "✅ Giveaway में successfully join हो गए!",
        show_alert=True
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 JOIN CHANNEL",
                url=CHANNEL_LINK
            )
        ],
        [
            InlineKeyboardButton(
                "🎁 JOIN GIVEAWAY",
                callback_data="join"
            )
        ],
    ]

    try:
        await query.edit_message_text(
            "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"
            f"💰 Prize: {PRIZE}\n"
            f"🏆 Winners: {WINNERS_COUNT}\n\n"
            "✅ Entry confirmed!\n\n"
            f"👥 Participants: {len(participants)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as error:
        logger.error(
            "Message update error: %s",
            error
        )


async def end_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global giveaway_active

    if not giveaway_active:
        await update.message.reply_text(
            "❌ कोई active giveaway नहीं है."
        )
        return

    if len(participants) < WINNERS_COUNT:
        await update.message.reply_text(
            f"❌ अभी सिर्फ {len(participants)} participants हैं.\n"
            f"कम से कम {WINNERS_COUNT} participants चाहिए."
        )
        return

    giveaway_active = False

    winners = random.sample(
        list(participants),
        WINNERS_COUNT
    )

    message = (
        "🎉 DAILY LOOT GIVEAWAY WINNERS 🎉\n\n"
        f"💰 Prize: {PRIZE}\n\n"
    )

    for number, user_id in enumerate(winners, start=1):

        try:
            user = await context.bot.get_chat(user_id)

            if user.username:
                name = f"@{user.username}"
            else:
                name = user.first_name or "Winner"

            message += (
                f"🏆 Winner {number}: {name}\n"
            )

        except Exception:
            message += (
                f"🏆 Winner {number}: User {user_id}\n"
            )

    message += (
        "\n🎁 Congratulations! 🎁\n"
        "\n❤️ Daily Loot Giveaway"
    )

    await update.message.reply_text(message)


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.error(
        "Bot error: %s",
        context.error
    )


def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN GitHub Secret में नहीं मिला."
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


if __name__ == "__main__":
    main()
