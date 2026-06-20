import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

waiting_user = None
pairs = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["💬 شروع چت ناشناس"],
        ["🔚 پایان چت", "❓ راهنما"]
    ]

    await update.message.reply_text(
        "😍 خوش اومدی به ربات چت ناشناس\n\nیک گزینه رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user

    user_id = update.message.from_user.id
    text = update.message.text

    if text == "❓ راهنما":
        await update.message.reply_text(
            "روی 💬 شروع چت ناشناس بزن تا یک نفر پیدا بشه."
        )
        return

    if text == "💬 شروع چت ناشناس":

        if user_id in pairs:
            await update.message.reply_text(
                "شما الان داخل چت هستی."
            )
            return

        if waiting_user is None:
            waiting_user = user_id
            await update.message.reply_text(
                "⏳ دنبال یک نفر می‌گردم..."
            )
        else:
            partner = waiting_user
            waiting_user = None

            pairs[user_id] = partner
            pairs[partner] = user_id

            await update.message.reply_text(
                "🎉 یک نفر پیدا شد، چت شروع شد!"
            )

            await context.bot.send_message(
                partner,
                "🎉 یک نفر پیدا شد، چت شروع شد!"
            )

        return

    if text == "🔚 پایان چت":

        if user_id in pairs:
            partner = pairs[user_id]

            del pairs[user_id]
            del pairs[partner]

            await update.message.reply_text(
                "چت شما پایان یافت."
            )

            await context.bot.send_message(
                partner,
                "طرف مقابل چت را پایان داد."
            )

        else:
            await update.message.reply_text(
                "شما داخل چتی نیستید."
            )

        return

    if user_id in pairs:
        partner = pairs[user_id]

        await context.bot.send_message(
            partner,
            text
        )
    else:
        await update.message.reply_text(
            "برای شروع چت روی 💬 شروع چت ناشناس بزن."
        )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

print("Bot is running...")
app.run_polling()
