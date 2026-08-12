import os
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

PRIZE = "₹100"
WINNERS_COUNT = 4

participants = set()
giveaway_active = False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 Welcome to Daily Loot Giveaway!\n\n"
        "💰 Prize: ₹100\n"
        "🏆 Winners: 4\n\n"
        "Use /giveaway to start a giveaway."
    )


async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants, giveaway_active

    participants.clear()
    giveaway_active = True

    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 JOIN GIVEAWAY",
                callback_data="join_giveaway"
            )
        ]
    ]

    await update.message.reply_text(
        "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"
        "💰 Prize: ₹100\n"
        "🏆 Winners: 4\n\n"
        "👇 Participate karne ke liye JOIN GIVEAWAY dabao.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer(
        "✅ Giveaway me successfully join ho gaye!"
    )

    user = query.from_user

    if not giveaway_active:
        await query.answer(
            "❌ Giveaway abhi active nahi hai.",
            show_alert=True
        )
        return

    if user.id in participants:
        await query.answer(
            "ℹ️ Aap already giveaway me joined ho.",
            show_alert=True
        )
        return

    participants.add(user.id)

    try:
        await query.edit_message_text(
            text=(
                "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"
                "💰 Prize: ₹100\n"
                "🏆 Winners: 4\n\n"
                f"👥 Participants: {len(participants)}\n\n"
                "👇 Join karne ke liye button dabao."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎁 JOIN GIVEAWAY",
                        callback_data="join_giveaway"
                    )
                ]
            ])
        )
    except Exception:
        pass


async def end_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global giveaway_active

    if not giveaway_active:
        await update.message.reply_text(
            "❌ Koi active giveaway nahi hai."
        )
        return

    giveaway_active = False

    if len(participants) < WINNERS_COUNT:
        await update.message.reply_text(
            f"❌ Sirf {len(participants)} participants hain.\n"
            f"{WINNERS_COUNT} winners ke liye kam se kam "
            f"{WINNERS_COUNT} participants chahiye."
        )
        return

    winners = random.sample(
        list(participants),
        WINNERS_COUNT
    )

    message = "🎉 DAILY LOOT GIVEAWAY WINNERS 🎉\n\n"

    for number, user_id in enumerate(winners, start=1):
        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name or "Winner"
            message += f"🏆 Winner {number}: {name}\n"
        except Exception:
            message += f"🏆 Winner {number}: User ID {user_id}\n"

    message += "\n💰 Prize: ₹100"
    message += "\n🎁 Congratulations! 🎉"

    await update.message.reply_text(message)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("giveaway", giveaway))
    app.add_handler(CommandHandler("end", end_giveaway))

    app.add_handler(
        CallbackQueryHandler(
            join_giveaway,
            pattern="^join_giveaway$"
        )
    )

    print("
