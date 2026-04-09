import os
import logging
from datetime import datetime, timedelta
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
    TOKEN = "8762946008:AAHRp1qgABwPUW9Urx66geTqC8y0xaAt3MI"  # for local testing only

# 🔗 GOOGLE DRIVE LINKS
DATA_LINK = "https://drive.google.com/drive/folders/1x1e_hpdVHKKjrqz2oEl56I4kV_SB9PBX?usp=drive_link"
CONTENT_LINK = "https://drive.google.com/drive/folders/12lNWAaKrN9zgG5jD_DZA6wlhaN0TK1Ta?usp=drive_link"
SCRIPT_LINK = "https://drive.google.com/drive/folders/1-HpKQHUABF8_lhxXdNmgKO7hujHxlk-L?usp=drive_link"
SCHEDULE_LINK = "https://drive.google.com/drive/folders/13Dweh3J14qH8o7v2MEd7I5M577-trxyn?usp=drive_link"

# Work tracking
work_sessions = {}
work_totals = {}

# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is live and ready.")

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📁 Main Drive:\n{DATA_LINK}")

async def client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clients = [
        "جينزي", "جادو", "شاورما يزن", "يلا نوكل",
        "الجيزاوي", "ابن سيرين", "لا كاسا",
        "زرب و زربيان", "الحوت", "زووم",
        "زورو", "هومييز", "واو", "تشيكن مان"
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
    await update.message.reply_text(
        "💼 Work Control:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def handle_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    name = user.first_name

    now = datetime.now()

    # CLOCK IN
    if query.data == "work_in":
        if user_id in work_sessions:
            await query.message.reply_text("⚠️ You already clocked in.")
            return

        work_sessions[user_id] = (now, name)
        await query.message.reply_text(f"🟢 Clocked IN at {now.strftime('%H:%M')}")

    # CLOCK OUT
    elif query.data == "work_out":
        session = work_sessions.get(user_id)

        if not session:
            await query.message.reply_text("❌ You didn't clock in.")
            return

        start_time, name = session
        duration = now - start_time

        if user_id not in work_totals:
            work_totals[user_id] = {"name": name, "time": timedelta()}

        work_totals[user_id]["time"] += duration

        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)

        await query.message.reply_text(
            f"🔴 Clocked OUT at {now.strftime('%H:%M')}\n"
            f"⏱ Session: {hours}h {minutes}m"
        )

        del work_sessions[user_id]

# ---------------- WORK REPORT ---------------- #

async def workreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not work_totals:
        await update.message.reply_text("📊 No work data yet.")
        return

    report = "📊 Work Report:\n\n"

    for user in work_totals.values():
        total_seconds = user["time"].total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        report += f"{user['name']} → {hours}h {minutes}m\n"

    await update.message.reply_text(report)

# ---------------- ERROR HANDLER ---------------- #

async def error_handler(update, context):
    logging.error(f"Error: {context.error}")

# ---------------- COMMAND MENU ---------------- #

async def set_commands(app):
    commands = [
        BotCommand("data", "Main drive link"),
        BotCommand("client", "View clients"),
        BotCommand("content", "Content folder"),
        BotCommand("script", "Script folder"),
        BotCommand("schedule", "Schedule folder"),
        BotCommand("work", "Clock in/out"),
        BotCommand("workreport", "Work report"),
    ]
    await app.bot.set_my_commands(commands)

# ---------------- RUN BOT ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("data", data))
app.add_handler(CommandHandler("client", client))
app.add_handler(CommandHandler("content", content))
app.add_handler(CommandHandler("script", script))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(CommandHandler("work", work))
app.add_handler(CommandHandler("workreport", workreport))

app.add_handler(CallbackQueryHandler(handle_work, pattern="^work_"))

app.add_error_handler(error_handler)
app.post_init = set_commands

logging.info("Bot is running...")
app.run_polling()
