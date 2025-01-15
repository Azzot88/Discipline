import os
from dotenv import load_dotenv
import telebot
from telebot.handler_backends import State as TeleState
from telebot import types
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
    CONTACT_SELECTION = 'contact_selection'
    SEARCHING_USERNAME = 'searching_username'
    SEARCHING_PHONE = 'searching_phone'

# Deal Types
class DealType:
    CHARITY = 'charity'
    DEBT = 'debt'
    SERVICE = 'service'
    VENTURE = 'venture'
