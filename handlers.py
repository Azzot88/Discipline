from config import bot, users, user_states, deals, State, DealType
from keyboards import *
from deal_manager import create_deal_group, setup_deal_chat, complete_deal
import logging

logger = logging.getLogger(__name__)

# Store temporary deal data
temp_deals = {}

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
    
    if message.chat.type == 'private':
        user_states[user_id] = State.SHARING_CONTACT
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton('📱 Share Contact', request_contact=True))
        
        bot.send_message(
            message.chat.id,
            "Welcome to DealVault Bot! 🎉\n\n"
            "To get started, please share your contact information.",
            reply_markup=keyboard
        )

@bot.message_handler(commands=['create_deal_group'])
def create_deal_group_command(message):
    user_id = message.from_user.id
    
    if not users.get(user_id, {}).get('is_registered'):
        bot.reply_to(
            message,
            "Please start private chat with me first and share your contact information.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("Start Private Chat", url=f"https://t.me/{bot.get_me().username}")
            )
        )
        return
    
    # Create inline keyboard for deal type selection
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("🤲 Charity", callback_data="create_charity"),
        types.InlineKeyboardButton("💰 Debt", callback_data="create_debt"),
        types.InlineKeyboardButton("🔧 Service", callback_data="create_service"),
        types.InlineKeyboardButton("💡 Venture", callback_data="create_venture")
    ]
    keyboard.add(*buttons)
    
    bot.reply_to(
        message,
        "Please select the type of deal you want to create:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def handle_deal_type_selection(call):
    user_id = call.from_user.id
    deal_type = call.data.replace('create_', '')
    
    # Store temporary deal info
    temp_deals[user_id] = {
        'type': deal_type,
        'creator_id': user_id,
        'status': 'pending'
    }
    
    # Ask for amount
    user_states[user_id] = State.ENTERING_AMOUNT
    bot.edit_message_text(
        "Please enter the deal amount:",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    for new_member in message.new_chat_members:
        if new_member.id == bot.get_me().id:
            # Bot was added to group
            bot.send_message(
                message.chat.id,
                "Thanks for adding me! This group will be used for deal communication.\n"
                "All members should start a private chat with me and share their contact information."
            )
        else:
            # New user joined
            if new_member.id not in users or not users[new_member.id].get('is_registered'):
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton(
                        "Share Contact (Private Chat)",
                        url=f"https://t.me/{bot.get_me().username}?start=register"
                    )
                )
                bot.send_message(
                    message.chat.id,
                    f"Welcome {new_member.first_name}! Please share your contact information "
                    f"by starting a private chat with me.",
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
        
        if message.chat.type == 'private':
            bot.send_message(
                message.chat.id,
                "Thanks for registering! You can now participate in deals.\n"
                "Use /create_deal_group to create a new deal.",
                reply_markup=get_main_menu()
            )
        user_states[user_id] = State.IDLE

# Add other necessary handlers...