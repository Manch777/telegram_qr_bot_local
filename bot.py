# ✅ Исправленный bot.py под Render Webhook
import os
import logging
import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from db import init_db, save_user, check_user, mark_checked_in, get_report
import pyqrcode
import io

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokens
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if not RENDER_EXTERNAL_HOSTNAME:
    raise ValueError("RENDER_EXTERNAL_HOSTNAME is missing!")

# Инициализация БД
init_db()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔗 Telegram канал", url="https://t.me/test1test123456test")],
        [InlineKeyboardButton("📸 Instagram", url="https://instagram.com/your_instagram")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Подпишитесь и нажмите кнопку ниже:", reply_markup=reply_markup)

# Проверка подписки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "no_username"
    is_subscribed = True  # Заглушка

    if is_subscribed:
        qr = pyqrcode.create(str(user_id))
        buffer = io.BytesIO()
        qr.png(buffer, scale=5)
        buffer.seek(0)

        save_user(user_id, username)
        await query.message.reply_photo(photo=buffer, caption="Вот ваш QR-код. Покажите его на входе.")
    else:
        await query.message.reply_text("❌ Вы не подписались на все каналы!")

# WebApp обработка
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.web_app_data:
        return

    data = update.message.web_app_data.data
    try:
        user_id = int(data.strip())
    except ValueError:
        await update.message.reply_text("❌ Неверный формат данных.")
        return

    if check_user(user_id):
        mark_checked_in(user_id)
        await update.message.reply_text(f"✅ Пользователь {user_id} найден и отмечен как пришедший.")
    else:
        await update.message.reply_text("❌ Пользователь не найден.")

# /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://manch777.github.io/qr-scanner/"
    keyboard = [[InlineKeyboardButton("📷 Открыть сканер", web_app=WebAppInfo(url=url))]]
    await update.message.reply_text("Сканируй QR-коды участников:", reply_markup=InlineKeyboardMarkup(keyboard))

# /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count, checked_in = get_report()
    await update.message.reply_text(f"👥 Зарегистрировано: {count}\n✅ Пришли: {checked_in}")

# MAIN
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^check$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_webapp_data))

    logger.info("🚀 Starting Webhook...")
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    asyncio.run(main())
