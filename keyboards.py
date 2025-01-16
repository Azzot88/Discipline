from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='📝 Create Deal')
    builder.button(text='👥 Active Deals')
    builder.button(text='📊 My Profile')
    builder.button(text='ℹ️ Help')
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='📱 Share Contact', request_contact=True)
    return builder.as_markup(resize_keyboard=True)

def get_deal_types_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='🤲 Charity')
    builder.button(text='💰 Debt')
    builder.button(text='🔧 Service')
    builder.button(text='💡 Venture')
    return builder.as_markup(resize_keyboard=True)

def get_settings_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='🔔 Notifications', callback_data='toggle_notifications')
    builder.button(text='🌐 Language', callback_data='change_language')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_registration_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='Register')
    return builder.as_markup(resize_keyboard=True)

def get_amount_selection_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='100 USDT')
    builder.button(text='200 USDT')
    builder.button(text='500 USDT')
    builder.button(text='1000 USDT')
    builder.button(text='Custom Amount')  # Option for custom amount
    return builder.as_markup(resize_keyboard=True)

def get_giver_selection_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='Select from Contacts')
    builder.button(text='Scan QR Code')
    return builder.as_markup(resize_keyboard=True)