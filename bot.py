import os
import random
import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = "@Zvtdrs4tPEdlYTJl"

PRIZE = "₹100"
WINNERS_COUNT = 4

participants = set()
giveaway_active = False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 Welcome to Daily Loot Giveaway!\n\n"
        "Giveaway Prize: ₹100\n"
        "Winners: 4\n\n"
        "Admin giveaway start karega."
    )


async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants, giveaway_active

    participants = set()
    giveaway_active = True

    keyboard = [
        [InlineKeyboardButton(
            "🎁 JOIN GIVEAWAY",
            callback_data="join"
        )]
    ]

    await update.message.reply_text(
        "🎁 DAILY LOOT GIVEAWAY\n\n"
        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"
        "👇 Giveaway me participate karne ke liye button dabao.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not giveaway_active:
        await query.answer(
            "❌ Giveaway abhi active nahi hai.",
            show_alert=True
        )
        return

    user = query.from_user
    participants.add(user.id)

    await query.answer(
        "✅ Aap giveaway me join ho gaye!",
        show_alert=True
    )


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
            f"❌ Sirf {len(participants)} participants hain. "
            f"{WINNERS_COUNT} winners select nahi ho sakte."
        )
        return

    winners = random.sample(
        list(participants),
        WINNERS_COUNT
    )

    text = "🎉 DAILY LOOT GIVEAWAY WINNERS 🎉\n\n"

    for number, user_id in enumerate(winners, 1):
        try:
            user = await context.bot.get_chat(user_id)
            name = user.first_name or "Winner"
            text += f"🏆 Winner {number}: {name}\n"
        except Exception:
            text += f"🏆 Winner {number}: User ID {user_id}\n"

    text += f"\n💰 Prize: {PRIZE}\n"
    text += "🎁 Congratulations! 🎉"

    await update.message.reply_text(text)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("giveaway", giveaway))
    app.add_handler(CommandHandler("end", end_giveaway))
    app.add_handler(CallbackQueryHandler(
        join_giveaway,
        pattern="^join$"
    ))

    print("🤖 Daily Loot Giveaway Bot Started!")

    app.run_polling()


if __name__ == "__main__":
    main()
