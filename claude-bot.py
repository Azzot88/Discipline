import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
from pathlib import Path  # Import Path for directory handling

from handlers import router
from middlewares import RegisterCheck
from data.data_manager import DataManager

# Load environment variables
load_dotenv()

# Create necessary directories for logging
log_dir = Path('data/logs')
log_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'bot.log'),  # Use the created directory
        logging.StreamHandler()
    ]
)

async def main():
    # Initialize data manager
    data_manager = DataManager()
    
    # Initialize bot and dispatcher
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Add data manager to dispatcher
    dp["data_manager"] = data_manager
    
    # Add middlewares
    dp.message.middleware(RegisterCheck())
    
    # Include routers
    dp.include_router(router)
    
    try:
        logging.info("Starting bot...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await data_manager.save_data()
        logging.info("Bot stopped")

if __name__ == '__main__':
    asyncio.run(main())