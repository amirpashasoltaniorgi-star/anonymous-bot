import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1430109772

waiting_user = None
pairs = {}

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()
cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    user_id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0
)
""")

conn.commit()

# ---------- USER SAVE ----------
def save_user(user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()


# ---------- FIND PARTNER ----------
async def find_partner(user_id, context):
    global waiting_user

    if waiting_user is None:
        waiting_user = user_id
        await context.bot.send_message(user_id, "⏳ دنبال یک نفر جدید می‌گردم...")
        return

    partner = waiting_user
    waiting_user = None

    if partner == user_id:
        waiting_user = user_id
        return

    pairs[user_id] = partner
    pairs[partner] = user_id

    await context.bot.send_message(user_id, "🎉 یک نفر پیدا شد!")
    await context.bot.send_message(partner, "🎉 یک نفر پیدا شد!")


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)

    keyboard = [
     
    ["💬 شروع چت ناشناس"],
        ["🔄 نفر بعدی"],
       ["🚨 گزارش کاربر"]
        ["🔚 پایان چت", "❓ راهنما"]
    ]

    await update.message.reply_text(
        "😍 به ربات چت ناشناس خوش اومدی",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# ---------- END CHAT ----------
async def end_chat(user_id, context, next_chat=False):
    global waiting_user

    if user_id == waiting_user:
        waiting_user = None

    if user_id in pairs:
        partner = pairs[user_id]

        del pairs[user_id]
        del pairs[partner]

        try:
            if next_chat:
                await context.bot.send_message(partner, "🔄 طرف مقابل رفت چت بعدی")
            else:
                await context.bot.send_message(partner, "🔚 طرف مقابل چت را ترک کرد")
        except:
            pass


# ---------- MESSAGE ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "❓ راهنما":
        await update.message.reply_text(
            "💬 شروع چت\n🔄 نفر بعدی\n🔚 پایان چت"
        )
        return

    if text == "💬 شروع چت ناشناس":
        if user_id in pairs:
            await update.message.reply_text("شما داخل چت هستید")
        else:
            await find_partner(user_id, context)
        return

    if text == "🔄 نفر بعدی":
        await end_chat(user_id, context, True)
        await find_partner(user_id, context)
        return

    if text == "🔚 پایان چت":
        await end_chat(user_id, context)
        await update.message.reply_text("🔚 از چت خارج شدی")
        return

    if user_id in pairs:
        partner = pairs[user_id]
        try:
            await context.bot.send_message(partner, text)
        except:
            await update.message.reply_text("❌ طرف مقابل قطع شد")
            await end_chat(user_id, context)
    else:
        await update.message.reply_text("اول شروع چت رو بزن")


# ---------- MEDIA ----------
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pairs:
        await update.message.reply_text("اول شروع چت کن")
        return

    partner = pairs[user_id]
    msg = update.message

    try:
        if msg.photo:
            await context.bot.send_photo(partner, msg.photo[-1].file_id, caption=msg.caption)

        elif msg.voice:
            await context.bot.send_voice(partner, msg.voice.file_id)

        elif msg.video:
            await context.bot.send_video(partner, msg.video.file_id, caption=msg.caption)

        elif msg.document:
            await context.bot.send_document(partner, msg.document.file_id, caption=msg.caption)

        elif msg.sticker:
            await context.bot.send_sticker(partner, msg.sticker.file_id)
    except:
        await update.message.reply_text("❌ ارسال ناموفق بود")


# ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    active_chats = len(pairs) // 2
    waiting = 1 if waiting_user else 0

    await update.message.reply_text(
        f"📊 پنل ادمین\n\n"
        f"👥 کاربران: {total_users}\n"
        f"💬 چت فعال: {active_chats}\n"
        f"⏳ در انتظار: {waiting}"
    )


# ---------- APP ----------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(
    filters.PHOTO | filters.VOICE | filters.VIDEO | filters.Document.ALL | filters.Sticker.ALL,
    handle_media
))

print("🔥 Bot is running...")
app.run_polling()
