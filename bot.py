# ✅ Полный bot.py для python-telegram-bot v20.7 (совместим с WebApp + QR + Render)

import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from db import init_db, save_user, check_user, mark_checked_in, get_report
from telegram.ext import CallbackQueryHandler
import pyqrcode
import io

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing! Set it in environment variables.")

# Инициализация БД
init_db()

# 📌 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔗 Telegram канал", url="https://t.me/test1test123456test")],
        [InlineKeyboardButton("📸 Instagram", url="https://instagram.com/your_instagram")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Подпишитесь и нажмите кнопку ниже:", reply_markup=reply_markup)

# 📌 Проверка подписки (заглушка)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "no_username"

    # Здесь должна быть реальная проверка подписки (заглушка):
    is_subscribed = True

    if is_subscribed:
        # Генерируем QR
        qr = pyqrcode.create(str(user_id))
        buffer = io.BytesIO()
        qr.png(buffer, scale=5)
        buffer.seek(0)

        save_user(user_id, username)
        await query.message.reply_photo(photo=buffer, caption="Вот ваш QR-код. Покажите его на входе.")
    else:
        await query.message.reply_text("❌ Вы не подписались на все каналы!")

# 📌 Обработка данных из WebApp QR сканера
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message.web_app_data:
        return

    data = update.effective_message.web_app_data.data  # данные из сканера
    user_id = int(data)
    if check_user(user_id):
        mark_checked_in(user_id)
        await update.message.reply_text(f"✅ Пользователь {user_id} найден и отмечен как пришедший.")
    else:
        await update.message.reply_text("❌ Пользователь не найден.")

# 📌 /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://qr-scanner-nine-pink.vercel.app/"  # заменить
    keyboard = [[InlineKeyboardButton("📷 Открыть сканер", web_app=WebAppInfo(url=url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Сканируй QR-коды участников:", reply_markup=reply_markup)

# 📌 /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count, checked_in = get_report()
    await update.message.reply_text(f"👥 Зарегистрировано: {count}\n✅ Пришли: {checked_in}")

# 📌 Запуск бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("report", report))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_PHOTO, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.MESSAGE_AUTO_DELETE_TIMER_CHANGED, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.PROXIMITY_ALERT_TRIGGERED, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_STARTED, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_ENDED, start))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_SCHEDULED, start))
    # 👇 Callback обработчик — ДО MessageHandler
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^check$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.COMMAND, start))

    # 👇 Только если нужен WebApp
    app.add_handler(MessageHandler(filters.ALL, handle_webapp_data))
    
    logger.info("Bot started successfully")
    app.run_polling()


if __name__ == "__main__":
    main()
