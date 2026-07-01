import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator
from config import TOKEN

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user mode per user ID
user_mode = {}

# Keyboard layout
keyboard = [["EN → KM", "KM → EN"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    user_mode[user_id] = "EN → KM"

    await update.message.reply_text(
        "👋 Welcome to the KM ↔ EN Translator Bot!\n\n"
        "📌 Choose a translation mode below:\n"
        "• EN → KM : English to Khmer\n"
        "• KM → EN : Khmer to English\n\n"
        "Then just type any text to translate it!",
        reply_markup=reply_markup
    )


# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "ℹ️ How to use this bot:\n\n"
        "1️⃣ Press /start to begin\n"
        "2️⃣ Choose a mode: EN → KM or KM → EN\n"
        "3️⃣ Type any text and I'll translate it!\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help  - Show this help message\n"
        "/mode  - Check your current mode",
        reply_markup=reply_markup
    )


# /mode command
async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    current_mode = user_mode.get(user_id, "EN → KM")

    await update.message.reply_text(
        f"🔄 Your current mode is: *{current_mode}*\n\n"
        "Use the buttons below to change it.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


# Handle mode selection buttons
async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    text = update.message.text
    user_mode[user_id] = text

    emoji = "🇬🇧➡️🇰🇭" if text == "EN → KM" else "🇰🇭➡️🇬🇧"

    await update.message.reply_text(
        f"{emoji} Mode set to: *{text}*\n\nNow send me any text to translate!",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


# Handle translation
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user or not update.effective_chat:
        return

    text = update.message.text
    if not text:
        return

    user_id = update.effective_user.id
    mode = user_mode.get(user_id, "EN → KM")

    # Show "typing..." action (null check fixes Pylance warning)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        if mode == "EN → KM":
            result = GoogleTranslator(source="en", target="km").translate(text)
            flag = "🇰🇭"
        else:
            result = GoogleTranslator(source="km", target="en").translate(text)
            flag = "🇬🇧"

        await update.message.reply_text(
            f"{flag} *Translation:*\n{result}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text(
            "❌ Translation failed. Please try again later.",
            reply_markup=reply_markup
        )


# Handle unknown commands
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(
        "❓ Unknown command. Type /help to see available commands.",
        reply_markup=reply_markup
    )


# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mode", mode_command))

    # Mode buttons — must be before translate handler
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^(EN → KM|KM → EN)$"),
        set_mode
    ))

    # Translate all other text messages
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(EN → KM|KM → EN)$"),
        translate
    ))

    # Unknown commands
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("✅ Bot is running...")
    print("✅ Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
