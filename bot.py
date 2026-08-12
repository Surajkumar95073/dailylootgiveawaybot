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
REQUIRED_REFERRALS = 3

participants = set()
referrals = {}
referred_by = {}
giveaway_active = False

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def referral_link(bot_username, user_id):
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Referral processing
    if context.args:
        argument = context.args[0]

        if argument.startswith("ref_"):
            try:
                referrer_id = int(argument.replace("ref_", ""))

                if (
                    referrer_id != user_id
                    and user_id not in referred_by
                ):
                    referred_by[user_id] = referrer_id

                    if referrer_id not in referrals:
                        referrals[referrer_id] = set()

                    referrals[referrer_id].add(user_id)

            except ValueError:
                pass

    me = await context.bot.get_me()

    link = referral_link(
        me.username,
        user_id
    )

    count = len(referrals.get(user_id, set()))

    await update.message.reply_text(
        "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"
        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"
        "📢 Channel join karo\n"
        f"👥 {REQUIRED_REFERRALS} friends refer karo\n"
        "🎁 Phir giveaway join karo.\n\n"
        f"👥 Your referrals: {count}/{REQUIRED_REFERRALS}\n\n"
        "🔗 Apna referral link:\n"
        f"{link}"
    )


async def giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global giveaway_active

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
        "📢 Step 1: Channel join karo\n"
        f"👥 Step 2: {REQUIRED_REFERRALS} friends refer karo\n"
        "🎁 Step 3: JOIN GIVEAWAY dabao\n\n"
        "⚠️ Dono conditions complete hona zaroori hai.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def join_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    user = query.from_user
    user_id = user.id

    if not giveaway_active:
        await query.answer(
            "❌ Giveaway active nahi hai.",
            show_alert=True
        )
        return

    # Channel check
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        if member.status in ("left", "kicked"):
            await query.answer(
                "❌ Pehle channel join karo!",
                show_alert=True
            )
            return

    except Exception as error:
        logger.error(
            "Channel check error: %s",
            error
        )

        await query.answer(
            "⚠️ Channel membership check nahi ho paya.",
            show_alert=True
        )
        return

    # Referral check
    referral_count = len(
        referrals.get(user_id, set())
    )

    if referral_count < REQUIRED_REFERRALS:
        remaining = (
            REQUIRED_REFERRALS - referral_count
        )

        await query.answer(
            f"❌ {remaining} aur friend refer karo!",
            show_alert=True
        )
        return

    # Already joined
    if user_id in participants:
        await query.answer(
            "ℹ️ Aap already giveaway me joined ho.",
            show_alert=True
        )
        return

    participants.add(user_id)

    await query.answer(
        "✅ Giveaway me successfully join ho gaye!",
        show_alert=True
    )

    await query.message.reply_text(
        "🎉 ENTRY CONFIRMED! 🎉\n\n"
        "✅ Channel joined\n"
        f"✅ {REQUIRED_REFERRALS} friends referred\n"
        "✅ Giveaway joined\n\n"
        "🍀 Best of luck!"
    )


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
            f"❌ Sirf {len(participants)} valid participants hain.\n"
            f"{WINNERS_COUNT} winners ke liye "
            f"{WINNERS_COUNT} participants chahiye."
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

    for number, user_id in enumerate(
        winners,
        start=1
    ):
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
        "\n🎁 Congratulations! 🎁"
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


if __name__ == "__main__":
    main()
