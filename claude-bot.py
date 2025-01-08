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
offers = {}
chats = {}
users = {}
user_states = {}

# States
class State:
    IDLE = 'idle'
    CREATING_OFFER = 'creating_offer'
    ENTERING_AMOUNT = 'entering_amount'
    ENTERING_TERMS = 'entering_terms'
    ENTERING_DURATION = 'entering_duration'
    SELECTING_FRIENDS = 'selecting_friends'
    IN_CHAT = 'in_chat'

# Helper function to create main menu keyboard
def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('📝 Create Offer'))
    keyboard.add(types.KeyboardButton('👥 My Active Deals'))
    keyboard.add(types.KeyboardButton('📊 My Profile'))
    return keyboard

# Start command handler
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    users[user_id] = {
        'username': message.from_user.username,
        'reputation': 0,
        'completed_deals': 0,
        'current_offer': None
    }
    user_states[user_id] = State.IDLE
    
    bot.send_message(
        message.chat.id,
        f"Welcome to P2P Lending Bot, {message.from_user.first_name}!\n"
        "What would you like to do?",
        reply_markup=get_main_menu()
    )

# Create offer handler
@bot.message_handler(func=lambda message: message.text == '📝 Create Offer')
def create_offer(message):
    user_id = message.from_user.id
    user_states[user_id] = State.ENTERING_AMOUNT
    
    bot.send_message(
        message.chat.id,
        "Please enter the amount you need:",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Amount handler
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_AMOUNT)
def handle_amount(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        users[user_id]['current_offer'] = {'amount': amount}
        user_states[user_id] = State.ENTERING_TERMS
        
        bot.send_message(
            message.chat.id,
            "Please describe your terms and conditions:"
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Please enter a valid number."
        )

# Terms handler
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_TERMS)
def handle_terms(message):
    user_id = message.from_user.id
    users[user_id]['current_offer']['terms'] = message.text
    user_states[user_id] = State.ENTERING_DURATION
    
    bot.send_message(
        message.chat.id,
        "Please enter the duration (in days):"
    )

# Duration handler
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == State.ENTERING_DURATION)
def handle_duration(message):
    user_id = message.from_user.id
    try:
        duration = int(message.text)
        users[user_id]['current_offer']['duration'] = duration
        user_states[user_id] = State.SELECTING_FRIENDS
        
        # Create inline keyboard for friend selection
        keyboard = types.InlineKeyboardMarkup()
        # Mock friends list (in production, implement proper friend system)
        mock_friends = [
            ('Friend 1', '1'),
            ('Friend 2', '2'),
            ('Friend 3', '3')
        ]
        
        for friend_name, friend_id in mock_friends:
            keyboard.add(types.InlineKeyboardButton(
                text=friend_name,
                callback_data=f"select_friend_{friend_id}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            text="✅ Confirm Selection",
            callback_data="confirm_friends"
        ))
        
        bot.send_message(
            message.chat.id,
            "Select friends to send the offer to:",
            reply_markup=keyboard
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Please enter a valid number of days."
        )

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data.startswith('select_friend_'):
        friend_id = call.data.split('_')[2]
        current_offer = users[user_id]['current_offer']
        if 'selected_friends' not in current_offer:
            current_offer['selected_friends'] = set()
        current_offer['selected_friends'].add(friend_id)
        
        bot.answer_callback_query(
            call.id,
            text=f"Friend {friend_id} selected!"
        )
    
    elif call.data == 'confirm_friends':
        current_offer = users[user_id]['current_offer']
        if 'selected_friends' not in current_offer or not current_offer['selected_friends']:
            bot.answer_callback_query(
                call.id,
                text="Please select at least one friend!"
            )
            return
        
        # Create offer
        offer_id = f"offer_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"
        offers[offer_id] = {
            'creator_id': user_id,
            'amount': current_offer['amount'],
            'terms': current_offer['terms'],
            'duration': current_offer['duration'],
            'status': 'pending',
            'invited_friends': list(current_offer['selected_friends'])
        }
        
        # Send invitations to selected friends
        for friend_id in current_offer['selected_friends']:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                text="Accept Offer",
                callback_data=f"accept_offer_{offer_id}"
            ))
            
            # In production, send to actual friend's chat_id
            bot.send_message(
                call.message.chat.id,  # This would be friend's chat_id in production
                f"New offer received!\n"
                f"Amount: {current_offer['amount']}\n"
                f"Terms: {current_offer['terms']}\n"
                f"Duration: {current_offer['duration']} days",
                reply_markup=keyboard
            )
        
        # Clear current offer and return to main menu
        users[user_id]['current_offer'] = None
        user_states[user_id] = State.IDLE
        
        bot.edit_message_text(
            "Offer sent to selected friends!",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(
            call.message.chat.id,
            "What would you like to do next?",
            reply_markup=get_main_menu()
        )
    
    elif call.data.startswith('accept_offer_'):
        offer_id = call.data.split('_')[2]
        offer = offers[offer_id]
        
        # Create chat for negotiation
        chat_id = f"chat_{offer_id}_{user_id}"
        chats[chat_id] = {
            'offer_id': offer_id,
            'participants': [offer['creator_id'], user_id],
            'status': 'active'
        }
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            text="Complete Deal",
            callback_data=f"complete_deal_{offer_id}"
        ))
        keyboard.add(types.InlineKeyboardButton(
            text="Cancel Deal",
            callback_data=f"cancel_deal_{offer_id}"
        ))
        
        bot.edit_message_text(
            f"Offer accepted! You can now discuss details.\n"
            f"Amount: {offer['amount']}\n"
            f"Terms: {offer['terms']}\n"
            f"Duration: {offer['duration']} days",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    
    elif call.data.startswith('complete_deal_'):
        offer_id = call.data.split('_')[2]
        offer = offers[offer_id]
        
        # Update offer status
        offer['status'] = 'completed'
        
        # Update user reputation
        creator_id = offer['creator_id']
        users[creator_id]['completed_deals'] += 1
        users[creator_id]['reputation'] += 1
        
        # Generate badge (mock)
        badge = {
            'type': 'completion_badge',
            'offer_id': offer_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'amount': offer['amount']
        }
        
        bot.edit_message_text(
            f"Deal completed successfully!\n"
            f"You've earned a completion badge! 🏆\n"
            f"Your reputation has increased.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(
            call.message.chat.id,
            "What would you like to do next?",
            reply_markup=get_main_menu()
        )

# Profile handler
@bot.message_handler(func=lambda message: message.text == '📊 My Profile')
def show_profile(message):
    user_id = message.from_user.id
    user = users.get(user_id, {
        'reputation': 0,
        'completed_deals': 0
    })
    
    bot.send_message(
        message.chat.id,
        f"Your Profile:\n"
        f"Reputation: ⭐️ {user['reputation']}\n"
        f"Completed Deals: 🤝 {user['completed_deals']}"
    )

# Active deals handler
@bot.message_handler(func=lambda message: message.text == '👥 My Active Deals')
def show_active_deals(message):
    user_id = message.from_user.id
    active_offers = [
        offer for offer in offers.values()
        if offer['creator_id'] == user_id and offer['status'] == 'pending'
    ]
    
    if not active_offers:
        bot.send_message(
            message.chat.id,
            "You don't have any active deals."
        )
        return
    
    for offer in active_offers:
        bot.send_message(
            message.chat.id,
            f"Offer ID: {offer['id']}\n"
            f"Amount: {offer['amount']}\n"
            f"Terms: {offer['terms']}\n"
            f"Duration: {offer['duration']} days\n"
            f"Status: {offer['status']}"
        )

# Error handler
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(
        message,
        "Sorry, I don't understand that command. Please use the menu buttons."
    )

# Start the bot
def main():
    print("Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()