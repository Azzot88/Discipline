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
        types.KeyboardButton("Подключиться к пользователю"),
        types.KeyboardButton("Завершить чат")
    )
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

# Обработчик нажатия кнопок
@bot.message_handler(func=lambda message: message.text == "Подключиться к пользователю")
def request_connection(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("Отмена"))
    bot.send_message(message.chat.id, "Введите ID пользователя, с которым хотите связаться, или нажмите 'Отмена':", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text.isdigit())
def connect_command(message):
    target_user_id = int(message.text)
    if target_user_id == message.chat.id:
        bot.send_message(message.chat.id, "Вы не можете связаться с самим собой.")
        return

    connections[message.chat.id] = target_user_id
    connections[target_user_id] = message.chat.id

    bot.send_message(message.chat.id, f"Вы связаны с пользователем {target_user_id}.")
    bot.send_message(target_user_id, f"С вами связался пользователь {message.chat.id}.")
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "Завершить чат")
def end_command(message):
    if message.chat.id in connections:
        target_user_id = connections.pop(message.chat.id)
        connections.pop(target_user_id, None)
        bot.send_message(target_user_id, "Чат завершён.")
        bot.send_message(message.chat.id, "Вы завершили чат.")
    else:
        bot.send_message(message.chat.id, "У вас нет активного чата.")
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "Отмена")
def cancel_action(message):
    bot.send_message(message.chat.id, "Действие отменено.")
    show_main_menu(message.chat.id)

# Пересылка сообщений между пользователями
@bot.message_handler(func=lambda message: message.chat.id in connections)
def forward_message(message):
    target_user_id = connections[message.chat.id]
    bot.send_message(target_user_id, message.text)

bot.polling()
