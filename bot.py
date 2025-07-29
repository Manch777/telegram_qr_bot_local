# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import pyqrcode
import os
import csv
from db import init_db, save_user, user_exists, get_all_users, mark_checked_in, is_checked_in

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_USERNAME = 'https://t.me/test1test123456test'
TELEGRAM_CHANNEL_LINK = f'https://t.me/test1test123456test'
INSTAGRAM_LINK = 'https://instagram.com/manch_artist'
ADMIN_IDS = [486487068]  # Замените на свой Telegram ID

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = (
        "👋 Привет!\n\n"
        "Чтобы получить скидочный QR-код:\n"
        "1️⃣ Подпишись на наш Telegram-канал и Instagram\n"
        "2️⃣ Нажми кнопку ниже для проверки"
    )
    keyboard = [
        [InlineKeyboardButton("📲 Telegram-канал", url=TELEGRAM_CHANNEL_LINK)],
        [InlineKeyboardButton("📸 Instagram", url=INSTAGRAM_LINK)],
        [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]
    ]
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))

def check_subscription(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    chat_id = query.message.chat.id
    query.answer()

    if user_exists(user_id):
        context.bot.send_message(chat_id=chat_id, text="✅ Вы уже получали QR-код.")
        return

    try:
        member = context.bot.get_chat_member(f"@{TELEGRAM_CHANNEL_USERNAME}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            qr_text = f"user_id:{user_id}"
            qr = pyqrcode.create(qr_text)
            file_path = f"{user_id}_qr.png"
            qr.png(file_path, scale=5)

            context.bot.send_photo(chat_id=chat_id, photo=open(file_path, 'rb'))
            context.bot.send_message(chat_id=chat_id, text="🎉 Всё готово! Покажите QR на входе.")
            save_user(user_id, user.username, user.first_name, user.last_name, qr_text)
            os.remove(file_path)
        else:
            context.bot.send_message(chat_id=chat_id, text="❌ Вы ещё не подписались на канал.")
    except Exception as e:
        context.bot.send_message(chat_id=chat_id, text="⚠️ Ошибка проверки.")
        print(e)

def admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if user_id not in ADMIN_IDS:
        context.bot.send_message(chat_id=chat_id, text="⛔ Доступ запрещен.")
        return
    keyboard = [
        [InlineKeyboardButton("📋 Все пользователи", callback_data="show_users")],
        [InlineKeyboardButton("📤 Экспорт CSV", callback_data="export_csv")],
        [InlineKeyboardButton("📷 Сканировать QR", web_app=WebAppInfo(url="https://manch777.github.io/qr-scanner/"))]
    ]
    context.bot.send_message(chat_id=chat_id, text="🛠 Админ-панель:", reply_markup=InlineKeyboardMarkup(keyboard))

def handle_admin_action(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    if user_id not in ADMIN_IDS:
        return
    query.answer()
    if query.data == "show_users":
        users = get_all_users()
        text = "\n".join([f"{u[0]} | {u[1] or ''} | {u[2] or ''} | {u[5][:10]} | {'✅' if u[6] else '❌'}" for u in users]) or "Нет пользователей."
        context.bot.send_message(chat_id=chat_id, text=f"👤 Пользователи:\n\n{text}")
    elif query.data == "export_csv":
        users = get_all_users()
        filename = "users_export.csv"
        with open(filename, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['user_id', 'username', 'first_name', 'last_name', 'qr_text', 'created_at', 'checked_in'])
            writer.writerows(users)
        context.bot.send_document(chat_id=chat_id, document=open(filename, "rb"))

def report(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if user_id not in ADMIN_IDS:
        context.bot.send_message(chat_id=chat_id, text="⛔ Доступ запрещен.")
        return
    users = get_all_users()
    total = len(users)
    checked_in_count = sum([1 for u in users if u[6] == 1])
    not_checked_in_count = total - checked_in_count
    context.bot.send_message(chat_id=chat_id, text=(
        f"📊 Отчет по посещаемости:\n"
        f"Всего пользователей: {total}\n"
        f"✅ Пришли: {checked_in_count}\n"
        f"❌ Не пришли: {not_checked_in_count}"
    ))

def handle_webapp_data(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.web_app_data.data.strip()
    if user_id not in ADMIN_IDS:
        return
    if text.startswith("user_id:") and text[8:].isdigit():
        scanned_id = int(text[8:])
        if user_exists(scanned_id):
            if is_checked_in(scanned_id):
                context.bot.send_message(chat_id=chat_id, text=f"ℹ️ Пользователь {scanned_id} уже отмечен как пришедший.")
            else:
                mark_checked_in(scanned_id)
                context.bot.send_message(chat_id=chat_id, text=f"✅ Пользователь {scanned_id} успешно отмечен на мероприятии.")
        else:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Пользователь {scanned_id} не найден в базе.")
    else:
        context.bot.send_message(chat_id=chat_id, text="❓ Неверный QR-код.")

def main():
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))
    dp.add_handler(CallbackQueryHandler(handle_admin_action, pattern="^(show_users|export_csv)$"))
    dp.add_handler(MessageHandler(Filters.web_app_data, handle_webapp_data))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
