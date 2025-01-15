from config import bot, users, user_states, deals, State, DealType
from keyboards import *
from deal_manager import create_new_deal, setup_deal_chat, complete_deal
from datetime import datetime

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
            'role': None
        }
    user_states[user_id] = State.SHARING_CONTACT
    
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
            "Thanks for registering! You can now use all bot features.",
            reply_markup=get_main_menu()
        )
        user_states[user_id] = State.IDLE

@bot.message_handler(func=lambda message: message.text == '📝 Create Deal')
def create_deal(message):
    user_id = message.from_user.id
    if not users[user_id].get('is_registered'):
        bot.reply_to(message, "Please register first using /start")
        return
    
    users[user_id]['current_deal'] = {}
    user_states[user_id] = State.SELECTING_DEAL_TYPE
    
    bot.send_message(
        message.chat.id,
        "Select deal type:",
        reply_markup=get_deal_types_keyboard()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.SELECTING_DEAL_TYPE)
def handle_deal_type(message):
    user_id = message.from_user.id
    deal_types = {
        '🤲 Charity': DealType.CHARITY,
        '💰 Debt': DealType.DEBT,
        '🔧 Service': DealType.SERVICE,
        '💡 Venture': DealType.VENTURE
    }
    
    if message.text in deal_types:
        users[user_id]['current_deal']['type'] = deal_types[message.text]
        user_states[user_id] = State.ENTERING_AMOUNT
        
        bot.send_message(
            message.chat.id,
            "Enter amount:",
            reply_markup=types.ReplyKeyboardRemove()
        )
    elif message.text == '↩️ Back':
        user_states[user_id] = State.IDLE
        bot.send_message(
            message.chat.id,
            "Returned to main menu",
            reply_markup=get_main_menu()
        )

@bot.message_handler(func=lambda message: message.text == '👥 Active Deals')
def show_active_deals(message):
    user_id = message.from_user.id
    active_deals = [deal for deal in deals.values() if 
                   (deal['creator_id'] == user_id or user_id in deal['invited_users']) and 
                   deal['status'] == 'active']
    
    if not active_deals:
        bot.send_message(
            message.chat.id,
            "You have no active deals.",
            reply_markup=get_main_menu()
        )
        return
    
    for deal in active_deals:
        deal_text = (
            f"Deal ID: {deal['id']}\n"
            f"Type: {deal['type']}\n"
            f"Amount: {deal['amount']}\n"
            f"Terms: {deal['terms']}\n"
            f"Duration: {deal['duration']} days"
        )
        bot.send_message(message.chat.id, deal_text)

@bot.message_handler(func=lambda message: message.text == '📊 My Profile')
def show_profile(message):
    user_id = message.from_user.id
    user = users[user_id]
    
    profile_text = (
        f"👤 Profile\n\n"
        f"Username: @{user['username']}\n"
        f"Reputation: ⭐ {user['reputation']}\n"
        f"Completed Deals: 🤝 {user['completed_deals']}"
    )
    
    bot.send_message(
        message.chat.id,
        profile_text,
        reply_markup=get_main_menu()
    )

def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"Error sending message: {e}")
        # Handle error appropriately

# ... (other handlers from original code)