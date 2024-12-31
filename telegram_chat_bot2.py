import telebot
from telebot import types
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Telegram bot token is missing. Please check your .env file.")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
active_chats = {}  # Tracks active chats: {chat_id: {partner, state}}
user_contacts = {}  # Tracks user-shared contacts: {user_id: {contact_id: contact_name}}

# Command /start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Привет! Используйте меню для работы с ботом.")
    bot.send_message(message.chat.id, f"Ваш Telegram ID: {message.chat.id}")
    show_main_menu(message.chat.id)

# Show main menu
def show_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📒 Пригласить пользователя в чат"))
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

# Invite user button handler
@bot.message_handler(func=lambda message: message.text == "📒 Пригласить пользователя в чат")
def invite_user_to_chat(message):
    user_id = message.chat.id

    if user_id in active_chats:
        bot.send_message(user_id, "Вы уже участвуете в чате. Завершите текущий чат перед созданием нового.")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_button = types.KeyboardButton("Поделиться контактами", request_contact=True)
    keyboard.add(contact_button)
    bot.send_message(user_id, "Нажмите кнопку ниже, чтобы поделиться контактами.", reply_markup=keyboard)

# Handle shared contact
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact is not None:
        user_id = message.chat.id
        contact_id = message.contact.user_id
        first_name = message.contact.first_name
        last_name = message.contact.last_name or ""

        # Save contact information
        if user_id not in user_contacts:
            user_contacts[user_id] = {}
        user_contacts[user_id][contact_id] = f"{first_name} {last_name}".strip()

        bot.send_message(user_id, "Контакт успешно добавлен!")
        show_main_menu(user_id)

# Get user contacts
def get_user_contacts(user_id):
    return user_contacts.get(user_id, {})

# Handle invitation
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

# Accept invite command
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

# Start chat
def start_chat(user1_id, user2_id):
    bot.send_message(user1_id, "Чат начался. Ожидайте вопросов.")
    bot.send_message(user2_id, "Чат начался. Ожидайте вопросов.")
    ask_question(user1_id, user2_id)

# Ask question in chat
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

# Main polling loop
bot.polling()
