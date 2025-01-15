from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
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

def get_deal_types_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='🤲 Charity', callback_data='create_charity')
    builder.button(text='💰 Debt', callback_data='create_debt')
    builder.button(text='🔧 Service', callback_data='create_service')
    builder.button(text='💡 Venture', callback_data='create_venture')
    builder.adjust(2)
    return builder.as_markup()

def get_start_bot_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Share Contact (Private Chat)", 
        url=f"https://t.me/{bot_username}?start=register"
    )
    return builder.as_markup()