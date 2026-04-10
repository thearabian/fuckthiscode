import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# GOOGLE DRIVE IMPORTS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

# ---------------- CONFIG ---------------- #

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("8762946008:AAHRp1qgABwPUW9Urx66geTqC8y0xaAt3MI")
if not TOKEN:
    TOKEN = "8762946008:AAHRp1qgABwPUW9Urx66geTqC8y0xaAt3MI"

# 🔗 GOOGLE DRIVE LINKS
DATA_LINK = "https://drive.google.com/drive/folders/1x1e_hpdVHKKjrqz2oEl56I4kV_SB9PBX?usp=drive_link"
CONTENT_LINK = "https://drive.google.com/drive/folders/12lNWAaKrN9zgG5jD_DZA6wlhaN0TK1Ta?usp=drive_link"
SCRIPT_LINK = "https://drive.google.com/drive/folders/1-HpKQHUABF8_lhxXdNmgKO7hujHxlk-L?usp=drive_link"
SCHEDULE_LINK = "https://drive.google.com/drive/folders/13Dweh3J14qH8o7v2MEd7I5M577-trxyn?usp=drive_link"

# 🔑 DRIVE API
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=credentials)

# 📂 FOLDER IDs (extract from your links)
CONTENT_FOLDER_ID = "12lNWAaKrN9zgG5jD_DZA6wlhaN0TK1Ta"
SCRIPT_FOLDER_ID = "1-HpKQHUABF8_lhxXdNmgKO7hujHxlk-L"

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
    clients = ["جينزي","جادو","شاورما يزن","يلا نوكل","الجيزاوي","ابن سيرين","لا كاسا","زرب و زربيان","الحوت","زووم","زورو","هومييز","واو","تشيكن مان"]
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
        await query.message.reply_text(f"🟢 IN {now.strftime('%H:%M')}")

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

# ---------------- WORK REPORT ---------------- #

async def workreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not work_totals:
        await update.message.reply_text("📊 No data.")
        return

    report = "📊 Work Report:\n\n"
    for user in work_totals.values():
        total = user["time"].total_seconds()
        report += f"{user['name']} → {int(total//3600)}h {int((total%3600)//60)}m\n"

    await update.message.reply_text(report)

# ---------------- DRIVE HELPERS ---------------- #

def get_drive_folders(parent_id):
    results = drive_service.files().list(
        q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

# ---------------- UPLOAD SYSTEM ---------------- #

async def uploadcontent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    folders = get_drive_folders(CONTENT_FOLDER_ID)

    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"content_{f['id']}")] for f in folders]

    await update.message.reply_text("📂 Choose content folder:", reply_markup=InlineKeyboardMarkup(keyboard))

async def uploadscript(update: Update, context: ContextTypes.DEFAULT_TYPE):
    folders = get_drive_folders(SCRIPT_FOLDER_ID)

    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"script_{f['id']}")] for f in folders]

    await update.message.reply_text("📝 Choose script folder:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_folder_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    folder_type, folder_id = query.data.split("_", 1)

    upload_state[user_id] = {
        "folder_id": folder_id,
        "type": folder_type,
        "step": "text"
    }

    await query.message.reply_text("✍️ Send your text")

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

    media = MediaInMemoryUpload(state["text"].encode("utf-8"), mimetype="text/plain")

    drive_service.files().create(
        body={"name": filename, "parents": [state["folder_id"]]},
        media_body=media
    ).execute()

    await update.message.reply_text(f"✅ Uploaded: {filename}")

    del upload_state[user_id]

# ---------------- RUN ---------------- #

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
app.add_handler(CallbackQueryHandler(handle_folder_choice, pattern="^(content|script)_"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))

logging.info("Bot is running...")
app.run_polling()
