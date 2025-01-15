import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from handlers import router
from middlewares import RegisterCheck

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    
    # Initialize storage
    storage = MemoryStorage()
    
    # Initialize dispatcher
    dp = Dispatcher(storage=storage)
    
    # Add middlewares
    dp.message.middleware(RegisterCheck())
    
    # Include routers
    dp.include_router(router)
    
    # Start polling
    logger.info("Starting bot...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())