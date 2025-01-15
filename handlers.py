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

def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"Error sending message: {e}")
        # Handle error appropriately

# ... (other handlers from original code)