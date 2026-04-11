import os
import logging
from datetime import datetime, timedelta
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ---------------- CONFIG ---------------- #

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    TOKEN = "PUT_YOUR_TOKEN_HERE"

# 🔗 GOOGLE DRIVE LINKS
DATA_LINK = "https://drive.google.com/drive/folders/1x1e_hpdVHKKjrqz2oEl56I4kV_SB9PBX?usp=drive_link"
CONTENT_LINK = "https://drive.google.com/drive/folders/12lNWAaKrN9zgG5jD_DZA6wlhaN0TK1Ta?usp=drive_link"
SCRIPT_LINK = "https://drive.google.com/drive/folders/1-HpKQHUABF8_lhxXdNmgKO7hujHxlk-L?usp=drive_link"
SCHEDULE_LINK = "https://drive.google.com/drive/folders/13Dweh3J14qH8o7v2MEd7I5M577-trxyn?usp=drive_link"

# ---------------- STATE ---------------- #

work_sessions = {}
work_totals = {}
upload_state = {}

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
    await update.message.reply_text(
        "💼 Work Control:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

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

        await query.message.reply_text(
            f"🔴 OUT\n⏱ {hours}h {minutes}m"
        )

        del work_sessions[user_id]

# ---------------- WORK REPORT ---------------- #

async def workreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not work_totals:
        await update.message.reply_text("📊 No work data yet.")
        return

    report = "📊 Work Report:\n\n"

    for user in work_totals.values():
        total = user["time"].total_seconds()
        hours = int(total // 3600)
        minutes = int((total % 3600) // 60)

        report += f"{user['name']} → {hours}h {minutes}m\n"

    await update.message.reply_text(report)

# ---------------- UPLOAD SYSTEM (NO CLOUD) ---------------- #

async def uploadcontent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upload_state[update.effective_user.id] = {
        "type": "content",
        "step": "text"
    }
    await update.message.reply_text("✍️ Send your content text")

async def uploadscript(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upload_state[update.effective_user.id] = {
        "type": "script",
        "step": "text"
    }
    await update.message.reply_text("✍️ Send your script text")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in upload_state:
        return

    state = upload_state[user_id]

    if state["step"] != "text":
        return

    state["text"] = update.message.text
    state["step"] = "name"

    await update.message.reply_text("📝 Send file name or type 'auto'")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in upload_state:
        return

    state = upload_state[user_id]

    if state["step"] != "name":
        return

    name_input = update.message.text

    if name_input.lower() == "auto":
        filename = f"{state['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    else:
        filename = f"{name_input}.txt"

    file = BytesIO(state["text"].encode("utf-8"))
    file.name = filename

    await update.message.reply_document(file)

    del upload_state[user_id]

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
        BotCommand("uploadcontent", "Upload content file"),
        BotCommand("uploadscript", "Upload script file"),
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
app.add_handler(CommandHandler("uploadcontent", uploadcontent))
app.add_handler(CommandHandler("uploadscript", uploadscript))

app.add_handler(CallbackQueryHandler(handle_work, pattern="^work_"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))

app.add_error_handler(error_handler)
app.post_init = set_commands

logging.info("Bot is running...")
app.run_polling()
