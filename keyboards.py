from telebot import types

def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('📝 Create Deal'),
        types.KeyboardButton('👥 Active Deals'),
        types.KeyboardButton('📊 My Profile'),
        types.KeyboardButton('ℹ️ Help')
    ]
    keyboard.add(*buttons)
    return keyboard

def get_deal_types_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('🤲 Charity'),
        types.KeyboardButton('💰 Debt'),
        types.KeyboardButton('🔧 Service'),
        types.KeyboardButton('💡 Venture'),
        types.KeyboardButton('↩️ Back')
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

def get_chat_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton('✅ Complete Deal'),
        types.KeyboardButton('❌ Cancel Deal'),
        types.KeyboardButton('↩️ Back to Main Menu')
    )
    return keyboard