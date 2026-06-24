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
CREATE TABLE IF NOT EXISTS genders (
    user_id INTEGER PRIMARY KEY,
    gender TEXT
)
""")

conn.commit()
cursor.execute("""
CREATE TABLE IF NOT EXISTS banned_users (
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
def is_banned(user_id):
    cursor.execute(
        "SELECT user_id FROM banned_users WHERE user_id=?",
        (user_id,)
    )

    return cursor.fetchone() is not None
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
    ["👦 پسر", "👧 دختر"],
    ["💬 شروع چت ناشناس"],
    ["🔄 نفر بعدی"],
    ["🚨 گزارش کاربر"],
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

    if text == "🚨 گزارش کاربر":
        if user_id not in pairs:
            await update.message.reply_text("❌ الان داخل چت نیستی")
            return

        partner = pairs[user_id]

        cursor.execute(
            "INSERT OR IGNORE INTO reports(user_id,count) VALUES(?,0)",
            (partner,)
        )

        cursor.execute(
            "UPDATE reports SET count=count+1 WHERE user_id=?",
            (partner,)
        )

        conn.commit()

        cursor.execute(
            "SELECT count FROM reports WHERE user_id=?",
            (partner,)
        )

        report_count = cursor.fetchone()[0]

        await update.message.reply_text(
            f"✅ گزارش ثبت شد\nتعداد گزارش: {report_count}"
        )

        await context.bot.send_message(
            ADMIN_ID,
            f"🚨 گزارش جدید\n\n"
            f"گزارش‌دهنده: {user_id}\n"
            f"کاربر گزارش‌شده: {partner}\n"
            f"تعداد گزارش‌ها: {report_count}"
        )

        return
    if text == "💬 شروع چت ناشناس":
        if user_id in pairs:
            await update.message.reply_text("شما داخل چت هستید")
        else:
            await find_partner(user_id, context)
        return


if text == "👦 پسر":
    cursor.execute(
        "INSERT OR REPLACE INTO genders(user_id, gender) VALUES(?, ?)",
        (user_id, "boy")
    )
    conn.commit()

    await update.message.reply_text(
        "✅ جنسیت شما روی پسر ثبت شد"
    )
    return

if text == "👧 دختر":
    cursor.execute(
        "INSERT OR REPLACE INTO genders(user_id, gender) VALUES(?, ?)",
        (user_id, "girl")
    )
    conn.commit()

    await update.message.reply_text(
        "✅ جنسیت شما روی دختر ثبت شد"
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
            await context.bot.send_photo(
                partner,
                msg.photo[-1].file_id,
                caption=msg.caption
            )

        elif msg.voice:
            await context.bot.send_voice(
                partner,
                msg.voice.file_id
            )

        elif msg.video:
            await context.bot.send_video(
                partner,
                msg.video.file_id,
                caption=msg.caption
            )

        elif msg.document:
            await context.bot.send_document(
                partner,
                msg.document.file_id,
                caption=msg.caption
            )

        elif msg.sticker:
            await context.bot.send_sticker(
                partner,
                msg.sticker.file_id
            )

    except Exception:
        await update.message.reply_text("❌ ارسال ناموفق بود")
    




    # ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    active_chats = len(pairs) // 2
    waiting = 1 if waiting_user else 0

    cursor.execute("""
    SELECT COUNT(*)
    FROM reports
    WHERE count >= 1
    """)
    reported_users = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COALESCE(SUM(count), 0)
    FROM reports
    """)
    total_reports = cursor.fetchone()[0]

    await update.message.reply_text(
        f"📊 پنل ادمین\n\n"
        f"👥 کاربران: {total_users}\n"
        f"💬 چت فعال: {active_chats}\n"
        f"⏳ در انتظار: {waiting}\n"
        f"🚨 کاربران گزارش‌شده: {reported_users}\n"
        f"📢 کل گزارش‌ها: {total_reports}"
    )
        
async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT user_id,count
    FROM reports
    ORDER BY count DESC
    LIMIT 20
    """)

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("هیچ گزارشی ثبت نشده")
        return

    text = "🚨 لیست گزارش‌ها\n\n"

    for user_id, count in rows:
        text += f"👤 {user_id} | {count} گزارش\n"

    await update.message.reply_text(text)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "استفاده:\n/broadcast متن پیام"
        )
        return

    message = " ".join(context.args)

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    sent = 0

    for user in users:
        try:
            await context.bot.send_message(
                user[0],
                f"📢 پیام مدیریت:\n\n{message}"
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(
        f"✅ پیام برای {sent} کاربر ارسال شد"
    )


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "استفاده:\n/ban user_id"
        )
        return

    user_id = int(context.args[0])

    cursor.execute(
        "INSERT OR IGNORE INTO banned_users(user_id) VALUES(?)",
        (user_id,)
    )

    conn.commit()

    await update.message.reply_text(
        f"✅ کاربر {user_id} بن شد"
    )
# ---------- APP ----------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("reports", reports))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("ban", ban))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(
    filters.PHOTO | filters.VOICE | filters.VIDEO | filters.Document.ALL | filters.Sticker.ALL,
    handle_media
))

print("🔥 Bot is running...")
app.run_polling()
