import os
import logging
from datetime import datetime, timedelta, time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------- CONFIG ---------------- #

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("8762946008:AAHRp1qgABwPUW9Urx66geTqC8y0xaAt3MI")
if not TOKEN:
    TOKEN = "8762946008:AAHRp1qgABwPUW9Urx66geTqC8y0xaAt3MI"

ADMIN_ID = 7969168763  # 🔴 PUT YOUR TELEGRAM ID

# 🔗 GOOGLE DRIVE LINKS
DATA_LINK = "https://drive.google.com/drive/folders/1x1e_hpdVHKKjrqz2oEl56I4kV_SB9PBX?usp=drive_link"
CONTENT_LINK = "https://drive.google.com/drive/folders/12lNWAaKrN9zgG5jD_DZA6wlhaN0TK1Ta?usp=drive_link"
SCRIPT_LINK = "https://drive.google.com/drive/folders/1-HpKQHUABF8_lhxXdNmgKO7hujHxlk-L?usp=drive_link"
SCHEDULE_LINK = "https://drive.google.com/drive/folders/13Dweh3J14qH8o7v2MEd7I5M577-trxyn?usp=drive_link"

# ⏰ WORK RULES
WORK_START_HOUR = 9
WORK_END_HOUR = 18
LATE_CHECK_MINUTE = 15

# ---------------- STATE ---------------- #

work_sessions = {}
work_totals = {}
daily_attendance = set()

# ---------------- BASIC COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is live and ready.")

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📁 Main Drive:\n{DATA_LINK}")

async def client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clients = [
        "جينزي","جادو","شاورما يزن","يلا نوكل",
        "الجيزاوي","ابن سيرين","لا كاسا",
        "زرب و زربيان","الحوت","زووم",
        "زورو","هومييز","واو","تشيكن مان"
    ]
    await update.message.reply_text("👥 Clients:\n" + "\n".join(clients))

async def content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📂 Content Folder:\n{CONTENT_LINK}")

async def script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📝 Script Folder:\n{SCRIPT_LINK}")

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📅 Schedule Folder:\n{SCHEDULE_LINK}")

# ---------------- WORK SYSTEM ---------------- #

async def work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 IN", callback_data="work_in")],
        [InlineKeyboardButton("🔴 OUT", callback_data="work_out")],
    ]
    await update.message.reply_text("💼 Work Control:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name
    now = datetime.now()

    if query.data == "work_in":
        if user_id in work_sessions:
            await query.message.reply_text("⚠️ Already clocked in.")
            return

        work_sessions[user_id] = (now, name)
        daily_attendance.add(user_id)

        await query.message.reply_text(f"🟢 IN at {now.strftime('%H:%M')}")

    elif query.data == "work_out":
        if user_id not in work_sessions:
            await query.message.reply_text("❌ Not clocked in.")
            return

        start_time, name = work_sessions[user_id]
        duration = now - start_time

        if user_id not in work_totals:
            work_totals[user_id] = {"name": name, "time": timedelta()}

        work_totals[user_id]["time"] += duration

        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)

        await query.message.reply_text(f"🔴 OUT\n⏱ {hours}h {minutes}m")

        del work_sessions[user_id]

# ---------------- ADMIN DASHBOARD ---------------- #

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized")
        return

    now = datetime.now()

    # Active workers
    active_text = ""
    for uid, (start_time, name) in work_sessions.items():
        duration = now - start_time
        h = int(duration.total_seconds() // 3600)
        m = int((duration.total_seconds() % 3600) // 60)
        active_text += f"{name} → {h}h {m}m (active)\n"

    if not active_text:
        active_text = "None"

    # Total
    total_text = ""
    for user in work_totals.values():
        total = user["time"].total_seconds()
        total_text += f"{user['name']} → {int(total//3600)}h {int((total%3600)//60)}m\n"

    if not total_text:
        total_text = "None"

    await update.message.reply_text(
        f"👑 ADMIN\n\n🟢 Active:\n{active_text}\n📊 Total:\n{total_text}"
    )

# ---------------- AUTO SYSTEM ---------------- #

async def check_late(context: ContextTypes.DEFAULT_TYPE):
    if not daily_attendance:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="⚠️ No one clocked in by 9:15 AM!"
        )

async def auto_clock_out(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()

    if not work_sessions:
        return

    msg = "🔴 AUTO CLOCK-OUT (6 PM)\n\n"

    for user_id, (start_time, name) in list(work_sessions.items()):
        duration = now - start_time

        if user_id not in work_totals:
            work_totals[user_id] = {"name": name, "time": timedelta()}

        work_totals[user_id]["time"] += duration

        h = int(duration.total_seconds() // 3600)
        m = int((duration.total_seconds() % 3600) // 60)

        msg += f"{name} → {h}h {m}m\n"

        del work_sessions[user_id]

    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

# ---------------- COMMAND MENU ---------------- #

async def set_commands(app):
    commands = [
        BotCommand("data", "Drive link"),
        BotCommand("client", "Clients"),
        BotCommand("content", "Content"),
        BotCommand("script", "Scripts"),
        BotCommand("schedule", "Schedule"),
        BotCommand("work", "Clock in/out"),
        BotCommand("workreport", "Report"),
        BotCommand("admin", "Admin panel"),
    ]
    await app.bot.set_my_commands(commands)

# ---------------- RUN ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("data", data))
app.add_handler(CommandHandler("client", client))
app.add_handler(CommandHandler("content", content))
app.add_handler(CommandHandler("script", script))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(CommandHandler("work", work))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(handle_work, pattern="^work_"))

app.post_init = set_commands

# ⏰ JOBS
job_queue = app.job_queue
job_queue.run_daily(check_late, time=time(hour=9, minute=15))
job_queue.run_daily(auto_clock_out, time=time(hour=18, minute=0))

logging.info("Bot is running...")
app.run_polling()
