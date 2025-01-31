from data.data_manager import DataManager
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatType
import logging
import asyncio
import uuid
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from config import User, DealType
from keyboards import get_main_menu, get_contact_keyboard, get_settings_keyboard, get_giver_selection_keyboard
from deal_manager import DealManager
from data.data_manager import DataManager
from models import DealType, Deal, DealStatus
from dataclasses import asdict

# Initialize logger
logger = logging.getLogger(__name__)

router = Router()

class DealStates(StatesGroup):
    entering_amount = State()
    entering_terms = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, data_manager=None):
    user_id = message.from_user.id
    if not data_manager.get_user(user_id):
        user = User(id=user_id, username=message.from_user.username)
        data_manager.save_user(user_id, user.to_dict())
    
    await state.clear()
    await message.answer(
        "Welcome to the DealBot! 🎉\n\n"
        "Here you can create and manage deals. Please register to get started.",
        reply_markup=get_registration_keyboard()  # Button to register
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
async def handle_contact(message: Message, state: FSMContext, data_manager=None):
    if not message.contact:
        await message.answer("No contact information received. Please try again.")
        return
        
    user_id = message.from_user.id
    contact = message.contact
    
    try:
        if user_id == contact.user_id:  # Verify the contact belongs to the user
            user_data = data_manager.get_user(user_id)
            if user_data:
                user = User.from_dict(user_data)
                user.phone = contact.phone_number
                user.first_name = contact.first_name
                user.last_name = contact.last_name
                user.is_registered = True
                
                # Update user data in the data manager
                data_manager.save_user(user_id, user.to_dict())
                
                await state.clear()
                await message.answer(
                    "Thanks for registering! You can now participate in deals.\n"
                    "Use the buttons below to navigate.",
                    reply_markup=get_main_menu()  # Ensure this is a button interaction
                )
            else:
                await message.answer("User data not found. Please restart the bot.")
        else:
            await message.answer("The contact does not belong to you. Please share your own contact.")
    except Exception as e:
        logger.error(f"Error handling contact: {e}")
        await message.answer("An error occurred while processing your contact. Please try again.")

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

@router.message(F.text == 'Register')
async def register_user(message: Message, state: FSMContext):
    await state.set_state('deal_selection')  # Set state for deal selection
    await message.answer(
        "Please choose a deal type:",
        reply_markup=get_deal_types_keyboard()  # Show deal types
    )

@router.message(F.text.in_(['Charity', 'Debt', 'Service', 'Venture']))
async def choose_deal_amount(message: Message, state: FSMContext):
    deal_type = message.text
    await state.update_data(deal_type=deal_type)  # Save deal type
    await state.set_state('amount_selection')  # Set state for amount selection
    await message.answer(
        "Please choose an amount:",
        reply_markup=get_amount_selection_keyboard()  # Show amount options
    )

@router.message(F.text.in_(['100 USDT', '200 USDT', '500 USDT', '1000 USDT', 'Custom Amount']))
async def select_giver(message: Message, state: FSMContext):
    amount = message.text
    await state.update_data(amount=amount)  # Save amount
    await state.set_state('giver_selection')  # Set state for giver selection
    await message.answer(
        "Please select a Savior from your contacts or scan a QR code.",
        reply_markup=get_giver_selection_keyboard()  # Show options for selecting Giver
    )

@router.message(F.text == 'Select from Contacts')
async def select_from_contacts(message: Message, state: FSMContext):
    # Logic to select a contact and create a deal
    await message.answer("Please select a Savior from your contacts or scan a QR code.")

@router.message(F.text == 'Savior Registration')
async def register_savior(message: Message, state: FSMContext):
    # Logic for Savior registration
    await message.answer("Savior registered successfully! You will receive the deal shortly.")

async def monitor_deal(deal_id):
    # Retrieve the deal from the data manager
    deal = data_manager.get_deal(deal_id)  # Assuming you have a method to get a deal by ID
    if not deal:
        logger.warning(f"Deal with ID {deal_id} not found.")
        return

    # Example of monitoring logic
    while True:
        # Check the current status of the deal
        current_status = deal['status']  # Assuming deal has a 'status' field

        if current_status == 'pending':
            # Notify the Initiator and Savior about the pending status
            initiator_id = deal['initiator_id']
            savior_id = deal['savior_id']
            await send_notification(initiator_id, f"Deal {deal_id} is still pending.")
            await send_notification(savior_id, f"Deal {deal_id} is still pending.")

        elif current_status == 'completed':
            # Notify both parties that the deal is completed
            await send_notification(initiator_id, f"Congratulations! Deal {deal_id} has been completed.")
            await send_notification(savior_id, f"Congratulations! Deal {deal_id} has been completed.")
            break  # Exit the loop if the deal is completed

        elif current_status == 'failed':
            # Notify both parties that the deal has failed
            await send_notification(initiator_id, f"Deal {deal_id} has failed.")
            await send_notification(savior_id, f"Deal {deal_id} has failed.")
            break  # Exit the loop if the deal has failed

        # Sleep for a certain period before checking again
        await asyncio.sleep(60)  # Check every 60 seconds

async def send_notification(user_id, message):
    # Logic to send a notification to the user
    await bot.send_message(user_id, message)  # Assuming you have access to the bot instance

@router.message(F.text.in_([DealType.CHARITY.value, DealType.DEBT.value, DealType.SERVICE.value, DealType.VENTURE.value]))
async def create_deal(message: Message, state: FSMContext, data_manager: DataManager):
    deal_type = DealType(message.text)
    user_id = message.from_user.id
    
    deal_amount = await state.get_data().get("deal_amount")
    
    deal = Deal(
        id=str(uuid.uuid4()),
        type=deal_type,
        amount=deal_amount,
        initiator=user_id,
    )
    
    deal_id = data_manager.create_deal(asdict(deal))
    
    await state.update_data(deal_id=deal_id)
    
    await message.answer("Deal created successfully!")

async def notify_user(user_id: str, message: str):
    try:
        await bot.send_message(user_id, message)
    except Exception as e:
        logging.error(f"Failed to send notification to user {user_id}: {str(e)}")

@router.callback_query(F.data == "accept_deal")
async def accept_deal(callback_query: CallbackQuery, state: FSMContext, data_manager: DataManager):
    deal_id = await state.get_data().get("deal_id")
    deal = data_manager.get_deal(deal_id)
    
    if deal["status"] != DealStatus.ACCEPTED.value:
        data_manager.update_deal(deal_id, {"status": DealStatus.ACCEPTED.value, "savior": callback_query.from_user.id})
        
        await notify_user(deal["initiator"], f"Your deal {deal_id} has been accepted!")
        await notify_user(callback_query.from_user.id, f"You have accepted deal {deal_id}!")
    
    await callback_query.answer("Deal accepted!")
