import telebot
from telebot import types
from dotenv import load_dotenv
import os
from datetime import datetime
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize bot
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

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
    SEARCHING_USERNAME = 'searching_username'
    SEARCHING_PHONE = 'searching_phone'
    CONTACT_SELECTION = 'contact_selection'

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

def get_user_search_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('🔍 Search by Username'),
        types.KeyboardButton('📱 Search by Phone'),
        types.KeyboardButton('↩️ Back to Main Menu')
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
            'role': None
        }
    user_states[user_id] = State.SHARING_CONTACT
    
    # Create contact request keyboard
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('📱 Share Contact', request_contact=True))
    
    bot.send_message(
        message.chat.id,
        "Welcome to DealVault Bot! 🎉\n\n"
        "To get started, please share your contact information.\n"
        "This will help others find you when creating deals.",
        reply_markup=keyboard
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    current_state = user_states.get(user_id)
    
    if message.contact is not None:
        if current_state == State.SHARING_CONTACT:
            # Handle initial registration
            users[user_id]['phone'] = message.contact.phone_number
            users[user_id]['is_registered'] = True
            users[user_id]['first_name'] = message.contact.first_name
            users[user_id]['last_name'] = message.contact.last_name
            
            bot.send_message(
                message.chat.id,
                "Thank you for sharing your contact! ✅\n\n"
                "You're all set to start making deals! 🤝",
                reply_markup=get_main_menu()
            )
            user_states[user_id] = State.IDLE
            
        elif current_state == State.CONTACT_SELECTION:
            # Handle friend selection
            contact = message.contact
            found_user = None
            
            # Search for user by phone number
            for uid, user_data in users.items():
                if (user_data.get('phone') == contact.phone_number and 
                    uid != user_id and 
                    user_data.get('is_registered')):
                    found_user = (uid, user_data)
                    break
            
            if found_user:
                # Add to selected friends
                current_deal = users[user_id]['current_deal']
                if 'selected_friends' not in current_deal:
                    current_deal['selected_friends'] = set()
                
                friend_id, friend_data = found_user
                current_deal['selected_friends'].add(friend_id)
                
                # Show current selection
                selected_names = []
                for fid in current_deal['selected_friends']:
                    user_data = users.get(int(fid), {})
                    name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
                    if user_data.get('username'):
                        name += f" (@{user_data['username']})"
                    selected_names.append(name)
                
                # Create keyboard for continuing or selecting more
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                keyboard.add(
                    types.KeyboardButton('👥 Select More Recipients', request_contact=True),
                    types.KeyboardButton('✅ Continue with Selected'),
                    types.KeyboardButton('↩️ Back to Main Menu')
                )
                
                selection_text = "Currently selected recipients:\n" + "\n".join(
                    f"• {name}" for name in selected_names
                )
                
                bot.send_message(
                    message.chat.id,
                    f"{selection_text}\n\nYou can select more recipients or continue with current selection.",
                    reply_markup=keyboard
                )
            else:
                bot.send_message(
                    message.chat.id,
                    "This contact is not registered in our system. Please select another contact.",
                    reply_markup=message.reply_markup
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

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_AMOUNT)
def handle_amount_entry(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
            
        users[user_id]['current_deal']['amount'] = amount
        user_states[user_id] = State.ENTERING_TERMS
        
        bot.send_message(
            message.chat.id,
            "Please enter the terms of your deal:",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Please enter a valid amount (number greater than 0)."
        )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_TERMS)
def handle_terms_entry(message):
    user_id = message.from_user.id
    
    # Store terms and move to duration state
    users[user_id]['current_deal']['terms'] = message.text
    user_states[user_id] = State.ENTERING_DURATION
    
    bot.send_message(
        message.chat.id,
        "Please enter the duration of the deal in days:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_DURATION)
def handle_duration_entry(message):
    user_id = message.from_user.id
    
    try:
        duration = int(message.text)
        if duration <= 0:
            raise ValueError
            
        users[user_id]['current_deal']['duration'] = duration
        user_states[user_id] = State.SELECTING_FRIENDS
        
        start_friend_selection(message)
        
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Please enter a valid number of days (positive integer)."
        )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.SELECTING_FRIENDS)
def start_friend_selection(message):
    user_id = message.from_user.id
    users[user_id]['current_deal']['selected_friends'] = set()
    
    # Create keyboard with contact selection button
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        types.KeyboardButton('👥 Select Recipients', request_contact=True),
        types.KeyboardButton('↩️ Back to Main Menu')
    )
    
    user_states[user_id] = State.CONTACT_SELECTION
    
    bot.send_message(
        message.chat.id,
        "Please select recipients for your deal:",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text == '🔍 Search by Username')
def search_by_username(message):
    user_id = message.from_user.id
    user_states[user_id] = State.SEARCHING_USERNAME
    
    bot.send_message(
        message.chat.id,
        "Please enter the username to search (without @ symbol):",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: message.text == '📱 Search by Phone')
def search_by_phone(message):
    user_id = message.from_user.id
    user_states[user_id] = State.SEARCHING_PHONE
    
    bot.send_message(
        message.chat.id,
        "Please enter the phone number to search (with country code):",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.SEARCHING_USERNAME)
def handle_username_search(message):
    user_id = message.from_user.id
    search_username = message.text.lower().strip()
    
    # Search in users dictionary
    found_users = []
    for uid, user_data in users.items():
        if (user_data.get('username', '').lower() == search_username and 
            uid != user_id and 
            user_data.get('is_registered')):
            found_users.append((uid, user_data))
    
    show_search_results(message.chat.id, found_users)
    # Reset state to SELECTING_FRIENDS after search
    user_states[user_id] = State.SELECTING_FRIENDS

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.SEARCHING_PHONE)
def handle_phone_search(message):
    user_id = message.from_user.id
    search_phone = message.text.strip().replace('+', '')
    
    # Search in users dictionary
    found_users = []
    for uid, user_data in users.items():
        if (user_data.get('phone', '').replace('+', '') == search_phone and 
            uid != user_id and 
            user_data.get('is_registered')):
            found_users.append((uid, user_data))
    
    show_search_results(message.chat.id, found_users)
    # Reset state to SELECTING_FRIENDS after search
    user_states[user_id] = State.SELECTING_FRIENDS

def show_search_results(chat_id, found_users):
    if not found_users:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("🔍 New Search", callback_data="new_search"),
            types.InlineKeyboardButton("✅ Done", callback_data="confirm_friends")
        )
        
        bot.send_message(
            chat_id,
            "No users found. Try a new search or finish selection.",
            reply_markup=keyboard
        )
        return

    # Create inline keyboard with found users
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for uid, user_data in found_users:
        user_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
        if user_data.get('username'):
            user_name += f" (@{user_data['username']})"
        
        keyboard.add(types.InlineKeyboardButton(
            text=user_name,
            callback_data=f"select_friend_{uid}"
        ))
    
    keyboard.add(
        types.InlineKeyboardButton("🔍 New Search", callback_data="new_search"),
        types.InlineKeyboardButton("✅ Done", callback_data="confirm_friends")
    )
    
    bot.send_message(
        chat_id,
        "Found users:\nClick to select/unselect users for your deal:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "new_search":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_friend_selection(call.message)
        
    elif call.data.startswith('select_friend_'):
        friend_id = call.data.split('_')[2]
        current_deal = users[user_id]['current_deal']
        
        if 'selected_friends' not in current_deal:
            current_deal['selected_friends'] = set()
            
        if friend_id in current_deal['selected_friends']:
            current_deal['selected_friends'].remove(friend_id)
            bot.answer_callback_query(call.id, "User removed from selection!")
        else:
            current_deal['selected_friends'].add(friend_id)
            bot.answer_callback_query(call.id, "User added to selection!")
        
        # Update the message to show current selection
        selected_names = []
        for fid in current_deal['selected_friends']:
            user_data = users.get(int(fid), {})
            name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
            if user_data.get('username'):
                name += f" (@{user_data['username']})"
            selected_names.append(name)
        
        selection_text = "Currently selected users:\n" + "\n".join(
            f"• {name}" for name in selected_names
        ) if selected_names else "No users selected"
        
        try:
            bot.edit_message_text(
                selection_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=call.message.reply_markup
            )
        except telebot.apihelper.ApiException:
            # Message is not modified, ignore the error
            pass
    
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

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.IN_CHAT)
def handle_chat_message(message):
    user_id = message.from_user.id
    current_deal = users[user_id]['current_deal']
    
    if current_deal and 'chat_with' in current_deal:
        other_user_id = current_deal['chat_with']
        bot.forward_message(other_user_id, message.chat.id, message.message_id)

# Add handler for continuing with selected friends
@bot.message_handler(func=lambda message: message.text == '✅ Continue with Selected')
def handle_selection_complete(message):
    user_id = message.from_user.id
    current_deal = users[user_id]['current_deal']
    
    if not current_deal.get('selected_friends'):
        bot.send_message(
            message.chat.id,
            "Please select at least one recipient for your deal.",
            reply_markup=message.reply_markup
        )
        return
    
    # Create confirmation keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("✅ Confirm Deal", callback_data="confirm_deal"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_deal")
    )
    
    # Show deal summary
    selected_names = []
    for fid in current_deal['selected_friends']:
        user_data = users.get(int(fid), {})
        name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
        if user_data.get('username'):
            name += f" (@{user_data['username']})"
        selected_names.append(name)
    
    summary = (
        f"Deal Summary:\n"
        f"Type: {current_deal['type']}\n"
        f"Amount: {current_deal['amount']}\n"
        f"Terms: {current_deal['terms']}\n"
        f"Duration: {current_deal['duration']} days\n\n"
        f"Recipients:\n" + "\n".join(f"• {name}" for name in selected_names)
    )
    
    bot.send_message(
        message.chat.id,
        summary,
        reply_markup=keyboard
    )

def main():
    print("DealVault Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()