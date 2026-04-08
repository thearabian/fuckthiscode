import os
import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------- CONFIG ---------------- #

logging.basicConfig(level=logging.INFO)

TOKEN = ("8762946008:AAHRp1qgABwPUW9Urx66geTqC8y0xaAt3MI")

if not TOKEN:
    TOKEN = "PUT_YOUR_TOKEN_HERE"  # fallback for local testing

work_sessions = {}

# ---------------- HELPERS ---------------- #

async def send_txt_files(update, folder):
    if not os.path.exists(folder):
        await update.message.reply_text(f"❌ {folder} folder not found.")
        return

    files = [f for f in os.listdir(folder) if f.endswith(".txt")]

    if not files:
        await update.message.reply_text("📭 No files found.")
        return

    for file in files:
        with open(os.path.join(folder, file), "rb") as f:
            await update.message.reply_document(f)

# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running 🚀")

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drive_link = "https://drive.google.com/drive/folders/1x1e_hpdVHKKjrqz2oEl56I4kV_SB9PBX?usp=drive_link"

    await update.message.reply_text(
        "📁 Access all files here:\n"
        f"{drive_link}\n\n"
        "⚡ Updated regularly"
    )

async def client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clients = ["جينزي", "جادو", "شاورما يزن","يلا نوكل","الجيزاوي","ابن سيرين","لا كاسا","زرب و زربيان","الحوت","زووم","زورو","هومييز","واو","تشيكن مان"]
    await update.message.reply_text("👥 Clients:\n" + "\n".join(clients))

async def content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_txt_files(update, "content")

async def script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_txt_files(update, "script")

# ---------------- SCHEDULE ---------------- #

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Abood", callback_data="abood")],
        [InlineKeyboardButton("Nadaaf", callback_data="nadaaf")],
        [InlineKeyboardButton("Client", callback_data="client_schedule")],
    ]
    await update.message.reply_text(
        "📅 Choose directory:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    folder_map = {
        "abood": "schedule/abood",
        "nadaaf": "schedule/nadaaf",
        "client_schedule": "schedule/client",
    }

    folder = folder_map.get(query.data)

    if not folder or not os.path.exists(folder):
        await query.message.reply_text("❌ Folder not found.")
        return

    files = [f for f in os.listdir(folder) if f.endswith(".txt")]

    if not files:
        await query.message.reply_text("📭 No files found in this folder.")
        return

    for file in files:
        with open(os.path.join(folder, file), "rb") as f:
            await query.message.reply_document(f)

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
    now = datetime.now()

    # CLOCK IN
    if query.data == "work_in":
        if user_id in work_sessions:
            await query.message.reply_text("⚠️ You already clocked in.")
            return

        work_sessions[user_id] = now
        await query.message.reply_text(f"🟢 Clocked IN at {now.strftime('%H:%M')}")

    # CLOCK OUT
    elif query.data == "work_out":
        start_time = work_sessions.get(user_id)

        if not start_time:
            await query.message.reply_text("❌ You didn't clock in.")
            return

        duration = now - start_time
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)

        await query.message.reply_text(
            f"🔴 Clocked OUT at {now.strftime('%H:%M')}\n"
            f"⏱ Worked: {hours}h {minutes}m"
        )

        del work_sessions[user_id]

# ---------------- ERROR HANDLER ---------------- #

async def error_handler(update, context):
    logging.error(f"Error: {context.error}")

# ---------------- COMMAND MENU ---------------- #

async def set_commands(app):
    commands = [
        BotCommand("data", "Get drive link"),
        BotCommand("client", "View clients"),
        BotCommand("content", "Get content files"),
        BotCommand("script", "Get scripts"),
        BotCommand("schedule", "View schedules"),
        BotCommand("work", "Clock in/out"),
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

app.add_handler(CallbackQueryHandler(handle_schedule, pattern="^(abood|nadaaf|client_schedule)$"))
app.add_handler(CallbackQueryHandler(handle_work, pattern="^work_"))

app.add_error_handler(error_handler)

app.post_init = set_commands

logging.info("Bot is running...")
app.run_polling()