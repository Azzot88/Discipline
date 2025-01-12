import telebot
from telebot import types
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Data storage
deals = {}
users = {}
user_states = {}

# Deal Types
class DealType:
    CHARITY = 'charity'
    DEBT = 'debt'
    SERVICE = 'service'
    VENTURE = 'venture'

# States
class State:
    IDLE = 'idle'
    SHARING_CONTACT = 'sharing_contact'
    SELECTING_DEAL_TYPE = 'selecting_deal_type'
    ENTERING_AMOUNT = 'entering_amount'
    ENTERING_TERMS = 'entering_terms'
    ENTERING_DURATION = 'entering_duration'
    SELECTING_FRIENDS = 'selecting_friends'
    IN_CHAT = 'in_chat'

def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('📝 Create Deal'),
        types.KeyboardButton('👥 Active Deals'),
        types.KeyboardButton('📊 My Profile'),
        types.KeyboardButton('ℹ️ Help')
    ]
    keyboard.add(*buttons)  # Unpacking buttons to create 2x2 grid
    return keyboard

def get_deal_types_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('🤲 Charity'),
        types.KeyboardButton('💰 Debt'),
        types.KeyboardButton('🔧 Service'),
        types.KeyboardButton('💡 Venture')
    ]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            'username': message.from_user.username,
            'reputation': 0,
            'completed_deals': 0,
            'current_deal': None,
            'phone': None,
            'is_registered': False,
            'role': None  # Will be either 'Initiator' or 'Savior'
        }
    user_states[user_id] = State.SHARING_CONTACT
    
    # Create contact request keyboard
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('📱 Share Contact', request_contact=True))
    
    bot.send_message(
        message.chat.id,
        "Welcome to DealVault Bot! 🎉\n\n"
        "To get started, please share your contact information.",
        reply_markup=keyboard
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if message.contact is not None:
        users[user_id]['phone'] = message.contact.phone_number
        users[user_id]['is_registered'] = True
        users[user_id]['first_name'] = message.contact.first_name
        users[user_id]['last_name'] = message.contact.last_name
        
        bot.send_message(
            message.chat.id,
            "Thank you for sharing your contact! ✅\n\n"
            "Wanna make a deal? 🤝",
            reply_markup=get_main_menu()
        )

@bot.message_handler(func=lambda message: message.text == '📝 Create Deal')
def create_deal(message):
    user_id = message.from_user.id
    
    if not users[user_id].get('is_registered'):
        bot.send_message(
            message.chat.id,
            "Please share your contact information first to create a deal.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            .add(types.KeyboardButton('📱 Share Contact', request_contact=True))
        )
        return
    
    users[user_id]['role'] = 'Initiator'
    user_states[user_id] = State.SELECTING_DEAL_TYPE
    bot.send_message(
        message.chat.id,
        "Please select the type of deal you want to create:",
        reply_markup=get_deal_types_keyboard()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.SELECTING_DEAL_TYPE)
def handle_deal_type_selection(message):
    user_id = message.from_user.id
    deal_type = None
    
    if message.text == '🤲 Charity':
        deal_type = DealType.CHARITY
    elif message.text == '💰 Debt':
        deal_type = DealType.DEBT
    elif message.text == '🔧 Service':
        deal_type = DealType.SERVICE
    elif message.text == '💡 Venture':
        deal_type = DealType.VENTURE
    
    if deal_type:
        users[user_id]['current_deal'] = {'type': deal_type}
        user_states[user_id] = State.ENTERING_AMOUNT
        bot.send_message(
            message.chat.id,
            "Please enter the amount or value of your deal:",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        bot.send_message(
            message.chat.id,
            "Please select a valid deal type.",
            reply_markup=get_deal_types_keyboard()
        )

def handle_deal_response(call):
    user_id = call.from_user.id
    deal_id = call.data.split('_')[2]
    
    if call.data.startswith('accept_deal'):
        users[user_id]['role'] = 'Savior'
        deals[deal_id]['savior_id'] = user_id
        deals[deal_id]['status'] = 'accepted'
        
        # Notify the Initiator
        initiator_id = deals[deal_id]['creator_id']
        bot.send_message(
            initiator_id,
            f"🎉 Good news! A Savior has accepted your deal!\n"
            f"Deal ID: {deal_id}"
        )
        
        bot.edit_message_text(
            "You've accepted the deal as a Savior! 🤝",
            call.message.chat.id,
            call.message.message_id
        )

bot.add_callback_query_handler(callback_handler)

# Add the rest of your existing code here (handle_duration, callback_handler, etc.)
# Just update the terminology to use "Initiator" and "Savior" in messages

def main():
    print("DealVault Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()