import telebot
from telebot import types
from dotenv import load_dotenv
import os
from datetime import datetime
import json

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Data storage (in production, use a proper database)

deals = {}  # was 'offers'
chats = {}
users = {}
user_states = {}

# States
class State:
    IDLE = 'idle'
    CREATING_DEAL = 'creating_deal' 
    ENTERING_AMOUNT = 'entering_amount'
    ENTERING_TERMS = 'entering_terms'
    ENTERING_DURATION = 'entering_duration'
    SELECTING_FRIENDS = 'selecting_friends'
    IN_CHAT = 'in_chat'
    SHARING_CONTACT = 'sharing_contact'

def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('📝 Create Deal')) 
    keyboard.add(types.KeyboardButton('👥 My Active Deals'))
    keyboard.add(types.KeyboardButton('📊 My Profile'))
    keyboard.add(types.KeyboardButton('📱 Share Contact', request_contact=True))
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            'username': message.from_user.username,
            'reputation': 0,
            'completed_deals': 0,
            ### UPDATED: Renamed field
            'current_deal': None,  
            'phone': None,
            'is_registered': False
        }
    user_states[user_id] = State.SHARING_CONTACT
    
    bot.send_message(
        message.chat.id,
        f"Welcome to DealVault Bot, {message.from_user.first_name}!\n"
        "To use the bot, please share your contact information first.",
        reply_markup=get_main_menu()
    )

@bot.message_handler(func=lambda message: message.text == '📝 Create Deal')
def create_deal(message):
    user_id = message.from_user.id
    
    if not users[user_id].get('is_registered'):
        bot.send_message(
            message.chat.id,
            "Please share your contact information first to create a deal.",
            reply_markup=get_main_menu()
        )
        return
    
    user_states[user_id] = State.ENTERING_AMOUNT
    bot.send_message(
        message.chat.id,
        "Please enter the amount you need:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_DURATION)
def handle_duration(message):
    user_id = message.from_user.id
    try:
        duration = int(message.text)
        users[user_id]['current_deal']['duration'] = duration
        user_states[user_id] = State.SELECTING_FRIENDS
        
        keyboard = create_users_keyboard(user_id)
        
        if len(get_registered_users(user_id)) == 0:
            bot.send_message(
                message.chat.id,
                "There are no registered users available. Please try again later.",
                reply_markup=get_main_menu()
            )
            user_states[user_id] = State.IDLE
            return
        
        bot.send_message(
            message.chat.id,
            "Select users to send the deal to:",
            reply_markup=keyboard
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Please enter a valid number of days."
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
            text=f"User selected!"
        )
    
    elif call.data == 'confirm_friends':
        handle_friend_confirmation(call)

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
        'invited_users': list(current_deal['selected_friends'])
    }
    
    # Send invitations to selected users
    creator_name = f"{users[user_id]['first_name']} {users[user_id]['last_name']}".strip()
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
                f"New deal received from {creator_name}!\n"
                f"Amount: {current_deal['amount']}\n"
                f"Terms: {current_deal['terms']}\n"
                f"Duration: {current_deal['duration']} days",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Failed to send message to user {friend_id}: {e}")
    
    # Clear current deal and return to main menu
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

@bot.message_handler(func=lambda message: message.text == '👥 My Active Deals')
def show_active_deals(message):
    user_id = message.from_user.id
    active_deals = [
        deal for deal in deals.values()
        if deal['creator_id'] == user_id and deal['status'] == 'pending'
    ]
    
    if not active_deals:
        bot.send_message(
            message.chat.id,
            "You don't have any active deals."
        )
        return
    
    for deal in active_deals:
        bot.send_message(
            message.chat.id,
            f"Deal ID: {deal['id']}\n"
            f"Amount: {deal['amount']}\n"
            f"Terms: {deal['terms']}\n"
            f"Duration: {deal['duration']} days\n"
            f"Status: {deal['status']}"
        )

# Start the bot
def main():
    print("DealVault Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()