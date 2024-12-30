import telebot
from telebot import types
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем значение переменной окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверяем, удалось ли загрузить токен
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Telegram bot token is missing. Please check your .env file.")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
connections = {}  # Хранит пары пользователей {user1_id: user2_id}
waiting_users = []  # Список ожидающих пользователей

# Команда /start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Привет! Используйте меню для работы с ботом.")
    bot.send_message(message.chat.id, f"Ваш Telegram ID: {message.chat.id}")
    show_main_menu(message.chat.id)

# Отображение основного меню
def show_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton("🔍 Найти пользователя"),
        types.KeyboardButton("❌ Завершить чат")
    )
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

# Обработчик кнопки поиска
@bot.message_handler(func=lambda message: message.text == "🔍 Найти пользователя")
def search_user(message):
    user_id = message.chat.id

    if user_id in connections:
        bot.send_message(user_id, "Вы уже связаны с пользователем. Завершите текущий чат перед поиском нового.")
        return

    if waiting_users:
        partner_id = waiting_users.pop(0)
        connections[user_id] = partner_id
        connections[partner_id] = user_id

        bot.send_message(user_id, f"👥 Найден пользователь! Вы теперь в чате с ID: {partner_id}")
        bot.send_message(partner_id, f"👥 Найден пользователь! Вы теперь в чате с ID: {user_id}")
    else:
        waiting_users.append(user_id)
        bot.send_message(user_id, "⌛ Ожидаем другого пользователя для соединения...")

# Обработчик завершения чата
@bot.message_handler(func=lambda message: message.text == "❌ Завершить чат")
def end_chat(message):
    user_id = message.chat.id

    if user_id in connections:
        partner_id = connections.pop(user_id)
        connections.pop(partner_id, None)

        bot.send_message(user_id, "Вы завершили чат.")
        bot.send_message(partner_id, "Ваш собеседник завершил чат.")
    else:
        bot.send_message(user_id, "У вас нет активного чата.")

    show_main_menu(user_id)

# Пересылка сообщений между пользователями
@bot.message_handler(func=lambda message: message.chat.id in connections)
def relay_message(message):
    user_id = message.chat.id
    partner_id = connections[user_id]

    bot.send_message(partner_id, message.text)

# Отмена действий
@bot.message_handler(func=lambda message: message.text == "Отмена")
def cancel_action(message):
    bot.send_message(message.chat.id, "Действие отменено.")
    show_main_menu(message.chat.id)

# Основной цикл работы бота
bot.polling()
