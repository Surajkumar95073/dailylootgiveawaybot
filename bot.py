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

# ==================================================
# SETTINGS
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = "@DailyLootGiveaway"
CHANNEL_LINK = "https://t.me/DailyLootGiveaway"

PRIZE = "₹100"
WINNERS_COUNT = 4
REQUIRED_REFERRALS = 3

# ==================================================
# ADMIN
# ==================================================

# GitHub Secret me ADMIN_ID add karna hoga.
# Agar abhi ADMIN_ID nahi hai to temporary 0 rakho.
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ==================================================
# DATA
# ==================================================

participants = set()

# user_id -> set of referred user IDs
referrals = {}

# referred_user_id -> referrer_user_id
referred_by = {}

giveaway_active = False

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ==================================================
# ADMIN CHECK
# ==================================================

def is_admin(user_id):
    return ADMIN_ID != 0 and user_id == ADMIN_ID


# ==================================================
# REFERRAL LINK
# ==================================================

async def get_referral_link(context, user_id):

    bot = await context.bot.get_me()

    return f"https://t.me/{bot.username}?start=ref_{user_id}"


# ==================================================
# CHANNEL CHECK
# ==================================================

async def is_channel_member(context, user_id):

    try:

        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as error:

        logger.error(
            "Channel membership error: %s",
            error
        )

        return False


# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    # -------------------------------
    # PROCESS REFERRAL
    # -------------------------------

    if context.args:

        argument = context.args[0]

        if argument.startswith("ref_"):

            try:

                referrer_id = int(
                    argument.replace("ref_", "")
                )

                # Self referral protection
                if referrer_id == user_id:
                    pass

                # Already referred
                elif user_id in referred_by:
                    pass

                else:

                    referred_by[user_id] = referrer_id

                    if referrer_id not in referrals:
                        referrals[referrer_id] = set()

                    referrals[referrer_id].add(user_id)

            except ValueError:
                pass

    # -------------------------------
    # REFERRAL LINK
    # -------------------------------

    link = await get_referral_link(
        context,
        user_id
    )

    referral_count = len(
        referrals.get(user_id, set())
    )

    # -------------------------------
    # BUTTONS
    # -------------------------------

    keyboard = [

        [
            InlineKeyboardButton(
                "🎁 GIVEAWAY",
                callback_data="show_giveaway"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 MY REFERRALS",
                callback_data="my_referrals"
            )
        ]

    ]

    await update.message.reply_text(

        "🎁 DAILY LOOT GIVEAWAY BOT 🎁\n\n"

        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"

        "📢 Channel join karo\n"
        f"👥 {REQUIRED_REFERRALS} friends refer karo\n\n"

        f"📊 Your Referrals: "
        f"{referral_count}/{REQUIRED_REFERRALS}\n\n"

        "🔗 Your Referral Link:\n"
        f"{link}",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================================
# SHOW GIVEAWAY
# ==================================================

async def show_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

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
                callback_data="join_giveaway"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 MY REFERRALS",
                callback_data="my_referrals"
            )
        ]

    ]

    await query.message.reply_text(

        "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"

        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"

        "📢 Step 1: Channel join karo\n"
        f"👥 Step 2: {REQUIRED_REFERRALS} friends refer karo\n"
        "🎁 Step 3: JOIN GIVEAWAY dabao\n\n"

        "⚠️ Dono conditions complete hona zaroori hai.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================================
# MY REFERRALS
# ==================================================

async def my_referrals(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = query.from_user
    user_id = user.id

    count = len(
        referrals.get(user_id, set())
    )

    link = await get_referral_link(
        context,
        user_id
    )

    if count >= REQUIRED_REFERRALS:

        status = "✅ REFERRAL REQUIREMENT COMPLETE"

    else:

        remaining = (
            REQUIRED_REFERRALS - count
        )

        status = (
            f"❌ {remaining} more referral(s) required"
        )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔄 CHECK AGAIN",
                callback_data="my_referrals"
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 JOIN GIVEAWAY",
                callback_data="join_giveaway"
            )
        ]

    ]

    await query.message.reply_text(

        "👥 MY REFERRALS\n\n"

        f"📊 Referrals: "
        f"{count}/{REQUIRED_REFERRALS}\n\n"

        f"{status}\n\n"

        "🔗 Your Referral Link:\n"
        f"{link}\n\n"

        "Apne friends ko ye link bhejo.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================================
# JOIN GIVEAWAY
# ==================================================

async def join_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user
    user_id = user.id

    # -------------------------------
    # GIVEAWAY ACTIVE CHECK
    # -------------------------------

    if not giveaway_active:

        await query.answer(
            "❌ Giveaway abhi active nahi hai.",
            show_alert=True
        )

        return

    # -------------------------------
    # CHANNEL CHECK
    # -------------------------------

    member = await is_channel_member(
        context,
        user_id
    )

    if not member:

        await query.answer(
            "❌ Pehle @DailyLootGiveaway channel join karo!",
            show_alert=True
        )

        return

    # -------------------------------
    # REFERRAL CHECK
    # -------------------------------

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

    # -------------------------------
    # DUPLICATE ENTRY CHECK
    # -------------------------------

    if user_id in participants:

        await query.answer(
            "ℹ️ Aap already giveaway me joined ho.",
            show_alert=True
        )

        return

    # -------------------------------
    # ADD PARTICIPANT
    # -------------------------------

    participants.add(user_id)

    await query.answer(
        "🎉 Entry confirmed!",
        show_alert=True
    )

    await query.message.reply_text(

        "🎉 ENTRY CONFIRMED 🎉\n\n"

        "✅ Channel joined\n"
        f"✅ {REQUIRED_REFERRALS} referrals completed\n"
        "✅ Giveaway joined\n\n"

        "🍀 Best of luck!\n\n"

        f"👥 Total participants: "
        f"{len(participants)}"

    )


# ==================================================
# ADMIN: START GIVEAWAY
# ==================================================

async def giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global giveaway_active

    user_id = update.effective_user.id

    if not is_admin(user_id):

        await update.message.reply_text(
            "❌ Sirf admin giveaway start kar sakta hai."
        )

        return

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
                callback_data="join_giveaway"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 MY REFERRALS",
                callback_data="my_referrals"
            )
        ]

    ]

    await update.message.reply_text(

        "🎁🎁 DAILY LOOT GIVEAWAY 🎁🎁\n\n"

        f"💰 PRIZE: {PRIZE}\n"
        f"🏆 WINNERS: {WINNERS_COUNT}\n\n"

        "📢 CHANNEL JOIN REQUIRED\n"
        f"👥 {REQUIRED_REFERRALS} FRIEND REFERRALS REQUIRED\n\n"

        "👇 Participate karne ke liye:\n"

        "1️⃣ Channel join karo\n"
        f"2️⃣ {REQUIRED_REFERRALS} friends refer karo\n"
        "3️⃣ JOIN GIVEAWAY dabao\n\n"

        "🍀 Good Luck!",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================================
# ADMIN: END GIVEAWAY
# ==================================================

async def end_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global giveaway_active

    user_id = update.effective_user.id

    if not is_admin(user_id):

        await update.message.reply_text(
            "❌ Sirf admin giveaway end kar sakta hai."
        )

        return

    if not giveaway_active:

        await update.message.reply_text(
            "❌ Koi active giveaway nahi hai."
        )

        return

    if len(participants) < WINNERS_COUNT:

        await update.message.reply_text(

            f"❌ Valid participants: "
            f"{len(participants)}\n\n"

            f"🏆 Required: "
            f"{WINNERS_COUNT}"

        )

        return

    giveaway_active = False

    winners = random.sample(
        list(participants),
        WINNERS_COUNT
    )

    message = (

        "🎉🎉 DAILY LOOT GIVEAWAY 🎉🎉\n\n"

        "🏆 WINNERS\n\n"

        f"💰 Prize: {PRIZE}\n\n"
    )

    for number, user_id in enumerate(
        winners,
        start=1
    ):

        try:

            user = await context.bot.get_chat(
                user_id
            )

            if user.username:

                name = f"@{user.username}"

            else:

                name = (
                    user.first_name
                    or "Winner"
                )

            message += (
                f"🏆 Winner {number}: "
                f"{name}\n"
            )

        except Exception:

            message += (
                f"🏆 Winner {number}: "
                f"User {user_id}\n"
            )

    message += (
        "\n🎁 Congratulations! 🎁\n"
        "\n❤️ Daily Loot Giveaway"
    )

    await update.message.reply_text(
        message
    )


# ==================================================
# ERROR HANDLER
# ==================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Bot error: %s",
        context.error
    )


# ==================================================
# MAIN
# ==================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
           
