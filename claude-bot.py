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

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data.startswith('select_friend_'):
        friend_id = call.data.split('_')[2]
        current_deal = users[user_id]['current_deal']
        if 'selected_friends' not in current_deal:
            current_deal['selected_friends'] = set()
        current_deal['selected_friends'].add(friend_id)
        
        bot.answer_callback_query(
            call.id,
            text="User selected!"
        )
    
    elif call.data == 'confirm_friends':
        handle_friend_confirmation(call)
    
    elif call.data.startswith('accept_deal'):
        handle_deal_response(call)

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

def handle_friend_confirmation(call):
    user_id = call.from_user.id
    current_deal = users[user_id]['current_deal']
    
    if 'selected_friends' not in current_deal or not current_deal['selected_friends']:
        bot.answer_callback_query(
            call.id,
            text="Please select at least one user!"
        )
        return
    
    # Create deal
    deal_id = f"deal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"
    deals[deal_id] = {
        'creator_id': user_id,
        'amount': current_deal['amount'],
        'terms': current_deal['terms'],
        'duration': current_deal['duration'],
        'status': 'pending',
        'type': current_deal['type'],
        'invited_users': list(current_deal['selected_friends'])
    }
    
    # Send invitations to selected users
    creator_name = f"{users[user_id].get('first_name', '')} {users[user_id].get('last_name', '')}".strip()
    if users[user_id].get('username'):
        creator_name += f" (@{users[user_id]['username']})"
    
    for friend_id in current_deal['selected_friends']:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            text="Accept Deal",
            callback_data=f"accept_deal_{deal_id}"
        ))
        
        try:
            bot.send_message(
                int(friend_id),
                f"New {current_deal['type']} deal received from {creator_name}!\n"
                f"Amount: {current_deal['amount']}\n"
                f"Terms: {current_deal['terms']}\n"
                f"Duration: {current_deal['duration']} days",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Failed to send message to user {friend_id}: {e}")
    
    users[user_id]['current_deal'] = None
    user_states[user_id] = State.IDLE
    
    bot.edit_message_text(
        "Deal sent to selected users!",
        call.message.chat.id,
        call.message.message_id
    )
    bot.send_message(
        call.message.chat.id,
        "What would you like to do next?",
        reply_markup=get_main_menu()
    )

def main():
    print("DealVault Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()