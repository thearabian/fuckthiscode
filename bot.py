import os
import logging
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

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

ADMIN_ID = 7969168763  # 🔴 PUT YOUR ID

TIMEZONE = ZoneInfo("Asia/Amman")

# 🔗 LINKS
DATA_LINK = "https://drive.google.com/drive/folders/1x1e_hpdVHKKjrqz2oEl56I4kV_SB9PBX"
CONTENT_LINK = "https://drive.google.com/drive/folders/12lNWAaKrN9zgG5jD_DZA6wlhaN0TK1Ta"
SCRIPT_LINK = "https://drive.google.com/drive/folders/1-HpKQHUABF8_lhxXdNmgKO7hujHxlk-L"
SCHEDULE_LINK = "https://drive.google.com/drive/folders/13Dweh3J14qH8o7v2MEd7I5M577-trxyn"

# ---------------- STATE ---------------- #

work_sessions = {}
work_totals = {}
daily_attendance = set()

# ---------------- BASIC ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is live.")

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(DATA_LINK)

async def content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CONTENT_LINK)

async def script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(SCRIPT_LINK)

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(SCHEDULE_LINK)

# ---------------- WORK ---------------- #

async def work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🟢 IN", callback_data="work_in")],
        [InlineKeyboardButton("🔴 OUT", callback_data="work_out")],
    ]
    await update.message.reply_text("Work Control:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    name = user.first_name
    now = datetime.now(TIMEZONE)

    # -------- IN --------
    if query.data == "work_in":
        if user_id in work_sessions:
            await query.message.reply_text("⚠️ Already IN")
            return

        work_sessions[user_id] = (now, name)
        daily_attendance.add(user_id)

        # Late penalty
        if now.hour > 9 or (now.hour == 9 and now.minute > 30):
            await query.message.reply_text("⚠️ Late! Half-day penalty.")

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 LATE: {name}"
            )

        await query.message.reply_text(f"🟢 IN {now.strftime('%H:%M')}")

    # -------- OUT --------
    elif query.data == "work_out":
        if user_id not in work_sessions:
            await query.message.reply_text("❌ Not IN")
            return

        start, name = work_sessions[user_id]
        duration = now - start

        if user_id not in work_totals:
            work_totals[user_id] = {"name": name, "time": timedelta()}

        work_totals[user_id]["time"] += duration

        h = int(duration.total_seconds() // 3600)
        m = int((duration.total_seconds() % 3600) // 60)

        await query.message.reply_text(f"🔴 OUT {h}h {m}m")

        del work_sessions[user_id]

# ---------------- ADMIN ---------------- #

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    now = datetime.now(TIMEZONE)

    active = ""
    for _, (start, name) in work_sessions.items():
        d = now - start
        active += f"{name} {int(d.total_seconds()//3600)}h\n"

    total = ""
    for u in work_totals.values():
        t = u["time"].total_seconds()
        total += f"{u['name']} {int(t//3600)}h\n"

    await update.message.reply_text(f"Active:\n{active or 'None'}\n\nTotal:\n{total or 'None'}")

# ---------------- FORCE ---------------- #

async def forcein(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])
    now = datetime.now(TIMEZONE)

    work_sessions[user_id] = (now, f"User {user_id}")
    await update.message.reply_text(f"Forced IN {user_id}")


async def forceout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])

    if user_id not in work_sessions:
        return

    start, name = work_sessions[user_id]
    now = datetime.now(TIMEZONE)

    duration = now - start

    if user_id not in work_totals:
        work_totals[user_id] = {"name": name, "time": timedelta()}

    work_totals[user_id]["time"] += duration

    del work_sessions[user_id]

    await update.message.reply_text(f"Forced OUT {user_id}")

# ---------------- WHOIS ---------------- #

async def whois(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await update.message.reply_text(
        f"ID: {user.id}\nName: {user.first_name}\n@{user.username}"
    )

# ---------------- AUTO SYSTEM ---------------- #

async def check_late(context: ContextTypes.DEFAULT_TYPE):
    if not daily_attendance:
        await context.bot.send_message(ADMIN_ID, "⚠️ No one clocked in")

async def auto_clock_out(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)

    if not work_sessions:
        return

    msg = "AUTO OUT\n"

    for uid, (start, name) in list(work_sessions.items()):
        d = now - start

        if uid not in work_totals:
            work_totals[uid] = {"name": name, "time": timedelta()}

        work_totals[uid]["time"] += d

        msg += f"{name}\n"

        del work_sessions[uid]

    await context.bot.send_message(ADMIN_ID, msg)


async def reset_daily(context: ContextTypes.DEFAULT_TYPE):
    daily_attendance.clear()

# ---------------- RUN ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("data", data))
app.add_handler(CommandHandler("content", content))
app.add_handler(CommandHandler("script", script))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(CommandHandler("work", work))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("forcein", forcein))
app.add_handler(CommandHandler("forceout", forceout))
app.add_handler(CommandHandler("whois", whois))

app.add_handler(CallbackQueryHandler(handle_work, pattern="^work_"))

# JOBS
job = app.job_queue
job.run_daily(check_late, time=time(9,15, tzinfo=TIMEZONE))
job.run_daily(auto_clock_out, time=time(18,0, tzinfo=TIMEZONE))
job.run_daily(reset_daily, time=time(0,0, tzinfo=TIMEZONE))

logging.info("Running...")
app.run_polling()
