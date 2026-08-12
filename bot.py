import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎁 Giveaway", callback_data="giveaway")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    await update.message.reply_text(
        "👋 Welcome to Daily Loot Giveaway Bot!\n\n"
        "🎁 Yahan future giveaways ke liye participate kar sakte ho.\n"
        "Neeche button choose karo.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 Giveaway section\n\n"
        "Abhi koi giveaway active nahi hai.\n"
        "Jab giveaway start hoga, yahin se participate kar sakoge."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Help\n\n"
        "/start - Bot start karein\n"
        "/giveaway - Current giveaway dekhein\n"
        "/help - Help message"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "giveaway":
        await query.message.reply_text(
            "🎁 Giveaway section\n\n"
            "Abhi koi giveaway active nahi hai."
        )
    elif query.data == "help":
        await query.message.reply_text(
            "ℹ️ Help\n\n"
            "/start - Bot start karein\n"
            "/giveaway - Current giveaway dekhein\n"
            "/help - Help message"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("giveaway", giveaway))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Daily Loot Giveaway Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
