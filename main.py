from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = TOKEN = "8925625127:AAHVClhRcFUrUw01b9H7wxrl31pv8MXz7Bw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام امیر 😎 ربات روشن شد!")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

print("Bot is running...")
app.run_polling()
