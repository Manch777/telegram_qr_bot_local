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
from db import init_db, save_user, check_user, mark_checked_in, get_report, get_all_users
from telegram.ext import CallbackQueryHandler
from dotenv import load_dotenv
import pyqrcode
import io

load_dotenv()
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    user_id = query.from_user.id
    username = query.from_user.username or "no_username"

    channels = ["@test1test123456test"]
    is_subscribed = True
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                is_subscribed = False
                break
        except Exception as e:
            logger.error(f"Ошибка при проверке подписки: {e}")
            is_subscribed = False
            break

    if is_subscribed:
        qr = pyqrcode.create(str(user_id))
        buffer = io.BytesIO()
        qr.png(buffer, scale=5)
        buffer.seek(0)

        save_user(user_id, username)
        await query.message.reply_photo(photo=buffer, caption="Вот ваш QR-код. Покажите его на входе.")
    else:
        await query.message.reply_text("❌ Вы не подписались на все каналы!")

    # ✅ Отвечаем на callback в конце — чтобы избежать timeouts
    await query.answer()



# 📌 Обработка данных из WebApp QR сканера

# Админский Telegram ID (замени на свой ID)
ADMIN_CHAT_ID = 486487068  # 👈 Вставь свой Telegram ID


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.web_app_data:
        return

    data = update.message.web_app_data.data
    try:
        user_id = int(data.strip())
    except ValueError:
        await update.message.reply_text("❌ Неверный формат данных.")
        return

    user_data = check_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден.")
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"❌ QR не найден: {user_id}")
        return

    checked_in = user_data["checked_in"] == 1
    username = user_data["username"]

    if checked_in:
        await update.message.reply_text("⚠️ Пользователь уже прошёл.")
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⚠️ {username} уже прошёл (ID: {user_id})")
    else:
        mark_checked_in(user_id)
        await update.message.reply_text(f"✅ Пользователь {username} найден и отмечен как пришедший.")
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"✅ {username} прошёл вход (ID: {user_id})")



    

# 📌 /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://manch777.github.io/qr-scanner/"  # заменить
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

    # 👉 Callback от Inline кнопки "Я подписался"
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^check$"))

    # 👉 WebApp-данные от MiniApp
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_webapp_data))

    # 👉 Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("report", report))

    # 👉 Другие Status Updates
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, start))

    logger.info("Bot started successfully")
    app.run_polling()


if __name__ == "__main__":
    main()
