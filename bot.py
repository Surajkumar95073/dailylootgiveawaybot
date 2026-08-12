import os
import random
import sqlite3
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_USERNAME = "@DailyLootGiveaway"
CHANNEL_LINK = "https://t.me/DailyLootGiveaway"

PRIZE = "₹100"
WINNERS_COUNT = 4
REQUIRED_REFERRALS = 3
DB_FILE = "giveaway.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# =========================
# DATABASE
# =========================

def db():
    con = sqlite3.connect(DB_FILE)

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT ''
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referred_id INTEGER PRIMARY KEY,
            referrer_id INTEGER NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            user_id INTEGER PRIMARY KEY
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    con.commit()
    return con


def register_user(user):
    con = db()

    con.execute(
        """
        INSERT OR REPLACE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (
            user.id,
            user.username or "",
            user.first_name or "",
        ),
    )

    con.commit()
    con.close()


def add_referral(referrer_id, referred_id):
    if referrer_id == referred_id:
        return False

    con = db()

    exists = con.execute(
        """
        SELECT referred_id
        FROM referrals
        WHERE referred_id = ?
        """,
        (referred_id,),
    ).fetchone()

    if exists:
        con.close()
        return False

    con.execute(
        """
        INSERT INTO referrals
        (referred_id, referrer_id)
        VALUES (?, ?)
        """,
        (
            referred_id,
            referrer_id,
        ),
    )

    con.commit()
    con.close()

    return True


def get_referral_count(user_id):
    con = db()

    row = con.execute(
        """
        SELECT COUNT(*)
        FROM referrals
        WHERE referrer_id = ?
        """,
        (user_id,),
    ).fetchone()

    con.close()

    return row[0]


def add_participant(user_id):
    con = db()

    con.execute(
        """
        INSERT OR IGNORE INTO participants
        (user_id)
        VALUES (?)
        """,
        (user_id,),
    )

    con.commit()
    con.close()


def is_participant(user_id):
    con = db()

    row = con.execute(
        """
        SELECT user_id
        FROM participants
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    con.close()

    return row is not None


def get_participants():
    con = db()

    rows = con.execute(
        """
        SELECT user_id
        FROM participants
        """
    ).fetchall()

    con.close()

    return [row[0] for row in rows]


def clear_participants():
    con = db()

    con.execute(
        "DELETE FROM participants"
    )

    con.commit()
    con.close()


def participant_count():
    con = db()

    row = con.execute(
        """
        SELECT COUNT(*)
        FROM participants
        """
    ).fetchone()

    con.close()

    return row[0]


def set_setting(key, value):
    con = db()

    con.execute(
        """
        INSERT OR REPLACE INTO settings
        (key, value)
        VALUES (?, ?)
        """,
        (
            key,
            value,
        ),
    )

    con.commit()
    con.close()


def get_setting(key, default="0"):
    con = db()

    row = con.execute(
        """
        SELECT value
        FROM settings
        WHERE key = ?
        """,
        (key,),
    ).fetchone()

    con.close()

    if row:
        return row[0]

    return default


def giveaway_active():
    return get_setting(
        "giveaway_active"
    ) == "1"


# =========================
# HELPERS
# =========================

def is_admin(user_id):
    return (
        ADMIN_ID != 0
        and user_id == ADMIN_ID
    )


async def referral_link(
    context,
    user_id,
):
    bot = await context.bot.get_me()

    return (
        f"https://t.me/{bot.username}"
        f"?start=ref_{user_id}"
    )


async def channel_joined(
    context,
    user_id,
):
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
        )

        return member.status in (
            "member",
            "administrator",
            "creator",
        )

    except Exception as error:
        logger.error(
            "Channel check failed: %s",
            error,
        )

        return False


def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎁 GIVEAWAY",
                    callback_data="giveaway_info",
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 MY REFERRALS",
                    callback_data="my_referrals",
                )
            ],
        ]
    )


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    register_user(user)

    if context.args:

        argument = context.args[0]

        if argument.startswith("ref_"):

            try:

                referrer_id = int(
                    argument[4:]
                )

                add_referral(
                    referrer_id,
                    user.id,
                )

            except ValueError:
                pass

    count = get_referral_count(
        user.id
    )

    link = await referral_link(
        context,
        user.id,
    )

    await update.message.reply_text(

        "🎁 DAILY LOOT GIVEAWAY BOT 🎁\n\n"

        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"

        "📢 Channel join karo\n"
        f"👥 {REQUIRED_REFERRALS} friends refer karo\n\n"

        f"📊 Your Referrals: "
        f"{count}/{REQUIRED_REFERRALS}\n\n"

        "🔗 Your Referral Link:\n"
        f"{link}",

        reply_markup=main_keyboard(),
    )


# =========================
# GIVEAWAY INFO
# =========================

async def giveaway_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📢 JOIN CHANNEL",
                    url=CHANNEL_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 JOIN GIVEAWAY",
                    callback_data="join_giveaway",
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 MY REFERRALS",
                    callback_data="my_referrals",
                )
            ],
        ]
    )

    await query.message.reply_text(

        "🎁 DAILY LOOT GIVEAWAY 🎁\n\n"

        f"💰 Prize: {PRIZE}\n"
        f"🏆 Winners: {WINNERS_COUNT}\n\n"

        "📢 Step 1: Channel join karo\n"
        f"👥 Step 2: {REQUIRED_REFERRALS} friends refer karo\n"
        "🎁 Step 3: JOIN GIVEAWAY dabao\n\n"

        "⚠️ Channel + referrals complete hona zaroori hai.",

        reply_markup=keyboard,
    )


# =========================
# MY REFERRALS
# =========================

async def my_referrals(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    count = get_referral_count(
        user_id
    )

    link = await referral_link(
        context,
        user_id,
    )

    if count >= REQUIRED_REFERRALS:

        status = (
            "✅ 3/3 referrals complete!"
        )

    else:

        remaining = (
            REQUIRED_REFERRALS - count
        )

        status = (
            f"❌ {remaining} aur referral chahiye."
        )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 CHECK AGAIN",
                    callback_data="my_referrals",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 JOIN GIVEAWAY",
                    callback_data="join_giveaway",
                )
            ],
        ]
    )

    await query.message.reply_text(

        "👥 MY REFERRALS\n\n"

        f"📊 Referrals: "
        f"{count}/{REQUIRED_REFERRALS}\n\n"

        f"{status}\n\n"

        "🔗 Tumhara referral link:\n"
        f"{link}\n\n"

        "Friends ko ye link bhejo.\n"
        "Har new user sirf ek baar count hoga.",

        reply_markup=keyboard,
    )


# =========================
# JOIN GIVEAWAY
# =========================

async def join_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    user_id = query.from_user.id

    if not giveaway_active():

        await query.answer(
            "❌ Giveaway abhi active nahi hai.",
            show_alert=True,
        )

        return

    if not await channel_joined(
        context,
        user_id,
    ):

        await query.answer(
            "❌ Pehle @DailyLootGiveaway channel join karo!",
            show_alert=True,
        )

        return

    count = get_referral_count(
        user_id
    )

    if count < REQUIRED_REFERRALS:

        await query.answer(
            f"❌ {REQUIRED_REFERRALS - count} "
            "aur referral chahiye!",
            show_alert=True,
        )

        return

    if is_participant(user_id):

        await query.answer(
            "ℹ️ Aap already giveaway me joined ho.",
            show_alert=True,
        )

        return

    add_participant(user_id)

    await query.answer(
        "🎉 Entry confirmed!",
        show_alert=True,
    )

    await query.message.reply_text(

        "🎉 ENTRY CONFIRMED 🎉\n\n"

        "✅ Channel joined\n"
        f"✅ {REQUIRED_REFERRALS} referrals completed\n"
        "✅ Giveaway joined\n\n"

        f"👥 Total participants: "
        f"{participant_count()}\n\n"

        "🍀 Best of luck!",
    )


# =========================
# ADMIN: GIVEAWAY
# =========================

async def giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Sirf admin giveaway start kar sakta hai."
        )

        return

    clear_participants()

    set_setting(
        "giveaway_active",
        "1",
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📢 JOIN CHANNEL",
                    url=CHANNEL_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 JOIN GIVEAWAY",
                    callback_data="join_giveaway",
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 MY REFERRALS",
                    callback_data="my_referrals",
                )
            ],
        ]
    )

    await update.message.reply_text(

        "🎁🎁 DAILY LOOT GIVEAWAY 🎁🎁\n\n"

        f"💰 PRIZE: {PRIZE}\n"
        f"🏆 WINNERS: {WINNERS_COUNT}\n\n"

        "📢 Channel join mandatory\n"
        f"👥 {REQUIRED_REFERRALS} friends referral mandatory\n\n"

        "1️⃣ Channel join karo\n"
        f"2️⃣ {REQUIRED_REFERRALS} friends refer karo\n"
        "3️⃣ JOIN GIVEAWAY dabao\n\n"

        "🍀 GOOD LUCK!",

        reply_markup=keyboard,
    )


# =========================
# ADMIN: END
# =========================

async def end_giveaway(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Sirf admin giveaway end kar sakta hai."
        )

        return

    if not giveaway_active():

        await update.message.reply_text(
            "❌ Koi active giveaway nahi hai."
        )

        return

    users = get_participants()

    if len(users) < WINNERS_COUNT:

        await update.message.reply_text(

            f"❌ Valid participants: "
            f"{len(users)}\n"

            f"🏆 Required: "
            f"{WINNERS_COUNT}"
        )

        return

    set_setting(
        "giveaway_active",
        "0",
    )

    winners = random.sample(
        users,
        WINNERS_COUNT,
    )

    message = (

        "🎉🎉 DAILY LOOT "
        "GIVEAWAY WINNERS 🎉🎉\n\n"

        f"💰 Prize: {PRIZE}\n\n"
    )

    for number, user_id in enumerate(
        winners,
        start=1,
    ):

        try:

            user = await context.bot.get_chat(
                user_id
            )

            if user.username:

                name = (
                    f"@{user.username}"
                )

            else:

                name = (
                    user.first_name
                    or "Winner"
                )

        except Exception:

            name = (
                f"User {user_id}"
            )

        message += (
            f"🏆 Winner {number}: "
            f"{name}\n"
        )

    message += (
        "\n🎁 Congratulations! 🎁\n"
        "❤️ Daily Loot Giveaway"
    )

    await update.message.reply_text(
        message
    )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update,
    context,
):

    logger.error(
        "Bot error: %s",
        context.error,
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN GitHub Secret me nahi mila."
        )

    db().close()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "giveaway",
            giveaway,
        )
    )

    app.add_handler(
        CommandHandler(
            "end",
            end_giveaway,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            giveaway_info,
            pattern="^giveaway_info$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            my_referrals,
            pattern="^my_referrals$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            join_giveaway,
            pattern="^join_giveaway$",
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "🤖 Daily Loot Giveaway Bot is running..."
    )

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
