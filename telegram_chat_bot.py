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
active_chats = {}  # Хранит чаты и участников {chat_id: {user1, user2}}

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
        types.KeyboardButton("📒 Пригласить пользователя в чат")
    )
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

# Обработчик кнопки приглашения пользователя
@bot.message_handler(func=lambda message: message.text == "📒 Пригласить пользователя в чат")
def invite_user_to_chat(message):
    user_id = message.chat.id

    if user_id in active_chats:
        bot.send_message(user_id, "Вы уже участвуете в чате. Завершите текущий чат перед созданием нового.")
        return

    keyboard = types.InlineKeyboardMarkup()
    contacts = get_user_contacts(user_id)

    if not contacts:
        bot.send_message(user_id, "У вас нет доступных контактов для выбора.")
        return

    for contact_id, contact_name in contacts.items():
        keyboard.add(types.InlineKeyboardButton(contact_name, callback_data=f"invite_{contact_id}"))

    bot.send_message(user_id, "Выберите пользователя для приглашения в чат:", reply_markup=keyboard)

# Обработка приглашения
@bot.callback_query_handler(func=lambda call: call.data.startswith("invite_"))
def handle_invite(call):
    inviter_id = call.message.chat.id
    invitee_id = int(call.data.split("_")[1])

    if inviter_id in active_chats:
        bot.send_message(inviter_id, "Вы уже участвуете в чате.")
        return

    bot.send_message(
        invitee_id,
        f"Пользователь {inviter_id} приглашает вас в чат. Примите приглашение с помощью /accept или отклоните с помощью /decline."
    )
    active_chats[inviter_id] = {"partner": invitee_id, "state": "pending"}
    bot.send_message(inviter_id, "Приглашение отправлено. Ожидайте ответа.")

# Обработка команды /accept
@bot.message_handler(commands=['accept'])
def accept_invite(message):
    user_id = message.chat.id
    for inviter_id, chat_data in active_chats.items():
        if chat_data["partner"] == user_id and chat_data["state"] == "pending":
            chat_data["state"] = "active"
            active_chats[user_id] = {"partner": inviter_id, "state": "active"}

            bot.send_message(inviter_id, "Ваше приглашение принято.")
            bot.send_message(user_id, "Вы присоединились к чату.")
            start_chat(inviter_id, user_id)
            return

    bot.send_message(user_id, "Нет активных приглашений.")

# Логика чата
def start_chat(user1_id, user2_id):
    bot.send_message(user1_id, "Чат начался. Ожидайте вопросов.")
    bot.send_message(user2_id, "Чат начался. Ожидайте вопросов.")
    ask_question(user1_id, user2_id)

def ask_question(user1_id, user2_id):
    question = "Как вас зовут?"
    bot.send_message(user1_id, f"Вопрос: {question}")
    bot.send_message(user2_id, f"Вопрос: {question}")
    active_chats[user1_id]["question"] = question
    active_chats[user2_id]["question"] = question

@bot.message_handler(func=lambda message: message.chat.id in active_chats)
def handle_answer(message):
    user_id = message.chat.id
    chat_data = active_chats[user_id]
    partner_id = chat_data["partner"]
    question = chat_data.get("question")

    if question:
        bot.send_message(partner_id, f"Ответ от {user_id}: {message.text}")
        bot.send_message(user_id, "Ответ получен.")
        del chat_data["question"]

        if "question" not in active_chats[partner_id]:
            bot.send_message(user_id, "Ожидаем ответа от вашего собеседника.")

# Заглушка для получения контактов
def get_user_contacts(user_id):
    return {
        123456789: "Контакт 1",
        987654321: "Контакт 2"
    }

# Основной цикл работы бота
bot.polling()