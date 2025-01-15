import telebot
from telebot import types
from enum import Enum
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

# Enums for state management
class State(Enum):
    IDLE = "idle"
    SHARING_CONTACT = "sharing_contact"
    SELECTING_DEAL_TYPE = "selecting_deal_type"
    ENTERING_AMOUNT = "entering_amount"
    ENTERING_TERMS = "entering_terms"
    ENTERING_DURATION = "entering_duration"
    SELECTING_FRIENDS = "selecting_friends"
    IN_CHAT = "in_chat"
    CONTACT_SELECTION = "contact_selection"

class DealType(Enum):
    CHARITY = "charity"
    DEBT = "debt"
    SERVICE = "service"
    VENTURE = "venture"

# Data classes for structured data
@dataclass
class UserProfile:
    phone: str
    username: str
    first_name: str
    last_name: str
    reputation: int = 0
    completed_deals: int = 0
    is_registered: bool = False

@dataclass
class Deal:
    id: str
    deal_type: DealType
    amount: float
    terms: str
    duration: int
    initiator_id: int
    recipients: List[int]
    chat_id: Optional[int] = None
    status: str = "active"
    created_at: datetime = datetime.now()

# Storage
users: Dict[int, UserProfile] = {}
deals: Dict[str, Deal] = {}
user_states: Dict[int, State] = {}
temp_deal_data: Dict[int, dict] = {}

# Initialize bot
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN)

# Keyboard layouts
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📝 Create Deal', '👥 Active Deals')
    markup.row('📊 My Profile', 'ℹ️ Help')
    return markup

def get_deal_type_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for deal_type in DealType:
        markup.row(deal_type.value.capitalize())
    markup.row('↩️ Back to Main Menu')
    return markup

def get_chat_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('✅ Complete Deal', callback_data='complete_deal'),
        types.InlineKeyboardButton('❌ Cancel Deal', callback_data='cancel_deal')
    )
    markup.row(types.InlineKeyboardButton('↩️ Back to Main Menu', callback_data='main_menu'))
    return markup

# Command handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in users:
        user_states[user_id] = State.SHARING_CONTACT
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = types.KeyboardButton("Share Contact", request_contact=True)
        markup.add(button)
        bot.reply_to(
            message,
            "Welcome! Please share your contact information to get started.",
            reply_markup=markup
        )
    else:
        bot.reply_to(
            message,
            "Welcome back!",
            reply_markup=get_main_menu()
        )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    contact = message.contact
    
    users[user_id] = UserProfile(
        phone=contact.phone_number,
        username=message.from_user.username or "",
        first_name=contact.first_name,
        last_name=contact.last_name or "",
        is_registered=True
    )
    
    user_states[user_id] = State.IDLE
    bot.reply_to(
        message,
        "Registration successful! What would you like to do?",
        reply_markup=get_main_menu()
    )

@bot.message_handler(func=lambda message: message.text == '📝 Create Deal')
def start_deal_creation(message):
    user_id = message.from_user.id
    if not users.get(user_id, None):
        bot.reply_to(message, "Please register first using /start")
        return
    
    user_states[user_id] = State.SELECTING_DEAL_TYPE
    temp_deal_data[user_id] = {}
    
    bot.reply_to(
        message,
        "What type of deal would you like to create?",
        reply_markup=get_deal_type_keyboard()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.SELECTING_DEAL_TYPE)
def handle_deal_type(message):
    user_id = message.from_user.id
    deal_type = message.text.lower()
    
    if deal_type not in [dt.value for dt in DealType]:
        bot.reply_to(message, "Please select a valid deal type.")
        return
    
    temp_deal_data[user_id]['deal_type'] = DealType(deal_type)
    user_states[user_id] = State.ENTERING_AMOUNT
    
    bot.reply_to(
        message,
        "Please enter the deal amount:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_AMOUNT)
def handle_amount(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        temp_deal_data[user_id]['amount'] = amount
        user_states[user_id] = State.ENTERING_TERMS
        
        bot.reply_to(message, "Please enter the deal terms:")
    except ValueError:
        bot.reply_to(message, "Please enter a valid positive number.")

def create_deal_chat(deal_id: str, initiator_id: int, recipient_id: int):
    # In a real implementation, you would:
    # 1. Create a new group chat
    # 2. Add both users to it
    # 3. Send initial deal information
    # For this example, we'll simulate it
    deal = deals[deal_id]
    chat_message = (
        f"Deal #{deal_id}\n"
        f"Type: {deal.deal_type.value}\n"
        f"Amount: {deal.amount}\n"
        f"Terms: {deal.terms}\n"
        f"Duration: {deal.duration} days"
    )
    
    bot.send_message(
        initiator_id,
        chat_message,
        reply_markup=get_chat_keyboard()
    )
    bot.send_message(
        recipient_id,
        chat_message,
        reply_markup=get_chat_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = call.from_user.id
    
    if call.data == 'complete_deal':
        # Handle deal completion
        users[user_id].reputation += 1
        users[user_id].completed_deals += 1
        bot.answer_callback_query(call.id, "Deal completed successfully!")
    elif call.data == 'cancel_deal':
        # Handle deal cancellation
        bot.answer_callback_query(call.id, "Deal cancelled.")
    elif call.data == 'main_menu':
        user_states[user_id] = State.IDLE
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "Main menu:", reply_markup=get_main_menu())

# Error handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    if user_id not in user_states:
        bot.reply_to(
            message,
            "Please start the bot using /start command.",
            reply_markup=types.ReplyKeyboardRemove()
        )

# Start the bot
def main():
    print("Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()
