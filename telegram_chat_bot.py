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
        types.KeyboardButton("📒 Выбрать пользователя из контактов"),
        types.KeyboardButton("❌ Завершить чат")
    )
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

# Обработчик кнопки выбора пользователя из контактов
@bot.message_handler(func=lambda message: message.text == "📒 Выбрать пользователя из контактов")
def select_user_from_contacts(message):
    user_id = message.chat.id

    if user_id in connections:
        bot.send_message(user_id, "Вы уже связаны с пользователем. Завершите текущий чат перед выбором нового.")
        return

    keyboard = types.InlineKeyboardMarkup()
    contacts = get_user_contacts(user_id)  # Функция для получения списка контактов пользователя

    if not contacts:
        bot.send_message(user_id, "У вас нет доступных контактов для выбора.")
        return

    for contact_id, contact_name in contacts.items():
        keyboard.add(types.InlineKeyboardButton(contact_name, callback_data=f"connect_{contact_id}"))

    bot.send_message(user_id, "Выберите пользователя из ваших контактов:", reply_markup=keyboard)

# Обработка нажатия на кнопку контакта
@bot.callback_query_handler(func=lambda call: call.data.startswith("connect_"))
def connect_to_contact(call):
    user_id = call.message.chat.id
    target_user_id = int(call.data.split("_")[1])

    if user_id in connections:
        bot.send_message(user_id, "Вы уже связаны с пользователем. Завершите текущий чат перед выбором нового.")
        return

    connections[user_id] = target_user_id
    connections[target_user_id] = user_id

    bot.send_message(user_id, f"Вы связаны с пользователем {target_user_id}.")
    bot.send_message(target_user_id, f"С вами связался пользователь {user_id}.")
    show_main_menu(user_id)

# Заглушка функции получения списка контактов пользователя
def get_user_contacts(user_id):
    # Здесь должна быть реализована логика для получения контактов пользователя.
    # Возвращаем словарь {contact_id: contact_name} для примера.
    return {
        123456789: "Контакт 1",
        987654321: "Контакт 2"
    }

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
