from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatType
from datetime import datetime

from config import User, DealType
from keyboards import get_main_menu, get_contact_keyboard, get_deal_types_keyboard, get_settings_keyboard
from deal_manager import DealManager

router = Router()

class DealStates(StatesGroup):
    entering_amount = State()
    entering_terms = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, data_manager=None):
    user_id = message.from_user.id
    if not data_manager.get_user(user_id):
        user = User(
            id=user_id,
            username=message.from_user.username
        )
        data_manager.save_user(user_id, user.to_dict())
    
    if message.chat.type == ChatType.PRIVATE:
        await state.clear()
        await message.answer(
            "Welcome to DealVault Bot! 🎉\n\n"
            "To get started, please share your contact information.",
            reply_markup=get_contact_keyboard()
        )

@router.message(Command('create_deal_group'))
async def cmd_create_deal(message: Message, state: FSMContext, data_manager=None):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    user_data = data_manager.get_user(message.from_user.id)
    if not user_data or not user_data.get('is_registered'):
        await message.answer("Please register first using /start")
        return
    
    await state.clear()
    await message.answer(
        "Please select the type of deal you want to create:",
        reply_markup=get_deal_types_keyboard()
    )

@router.callback_query(F.data.startswith('create_'))
async def process_deal_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # Acknowledge the callback
    
    deal_type = callback.data.replace('create_', '')
    
    await state.update_data(deal_type=deal_type)
    await state.set_state(DealStates.entering_amount)
    
    await callback.message.edit_text(
        "Please enter the deal amount:",
        reply_markup=None  # Remove inline keyboard
    )

@router.message(DealStates.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        await state.update_data(amount=amount)
        await state.set_state(DealStates.entering_terms)
        
        await message.answer("Please enter the deal terms:")
    except ValueError:
        await message.answer("Please enter a valid positive number.")

@router.message(DealStates.entering_terms)
async def process_terms(message: Message, state: FSMContext):
    data = await state.get_data()
    deal_id = await create_deal_group(
        message.from_user.id,
        data['deal_type'],
        data['amount'],
        message.text
    )
    
    if deal_id:
        await state.clear()
        await message.answer(
            "Deal created successfully! Please create a group and add me there.",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer("Error creating deal. Please try again.")

@router.message(F.content_type.in_({'new_chat_members'}))
async def on_new_member(message: Message):
    for member in message.new_chat_members:
        if member.id == message.bot.id:
            await message.answer(
                "Thanks for adding me! This group will be used for deal communication.\n"
                "All members should start a private chat with me and share their contact information."
            )
        else:
            if member.id not in users or not users[member.id].is_registered:
                bot_info = await message.bot.get_me()
                await message.answer(
                    f"Welcome {member.first_name}! Please share your contact information "
                    f"by starting a private chat with me.",
                    reply_markup=get_start_bot_keyboard(bot_info.username)
                )

@router.message(F.content_type.in_({'contact'}))
async def handle_contact(message: Message, state: FSMContext):
    if not message.contact:
        return
        
    user_id = message.from_user.id
    contact = message.contact
    
    if user_id == contact.user_id:  # Verify the contact belongs to the user
        users[user_id].phone = contact.phone_number
        users[user_id].first_name = contact.first_name
        users[user_id].last_name = contact.last_name
        users[user_id].is_registered = True
        
        await state.clear()
        await message.answer(
            "Thanks for registering! You can now participate in deals.\n"
            "Use /create_deal_group to create a new deal.",
            reply_markup=get_main_menu()
        )

@router.errors()
async def error_handler(update: types.Update, exception: Exception):
    logger.error(f"Update {update} caused error {exception}")
    if isinstance(update, Message):
        await update.answer("An error occurred while processing your request. Please try again.")

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Action cancelled", reply_markup=get_main_menu())

@router.message(Command("complete_deal"))
async def cmd_complete_deal(message: Message, data_manager=None):
    if message.chat.type != ChatType.GROUP:
        return
        
    deal = data_manager.get_deal_by_group(message.chat.id)
    if not deal:
        await message.answer("No active deal in this group")
        return
        
    # Add completion logic

@router.message(Command("settings"))
async def cmd_settings(message: Message, data_manager=None):
    user_data = data_manager.get_user(message.from_user.id)
    if user_data:
        user = User.from_dict(user_data)
        settings_text = (
            "Current Settings:\n"
            f"🔔 Notifications: {user.settings.notifications}\n"
            f"🌐 Language: {user.settings.language}"
        )
        await message.answer(settings_text, reply_markup=get_settings_keyboard())

@router.message()
async def update_user_activity(message: Message, data_manager=None):
    user_data = data_manager.get_user(message.from_user.id)
    if user_data:
        user = User.from_dict(user_data)
        user.last_active = datetime.now().isoformat()
        data_manager.save_user(message.from_user.id, user.to_dict())

# Add other necessary handlers...