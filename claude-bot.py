import time
import sys
import os
import logging
from datetime import datetime
from config import bot
import handlers
from deal_manager import *

# Create log directory in user's directory
log_dir = "/home/ubuntu/Discipline/logs"
os.makedirs(log_dir, exist_ok=True)

# Setup logging with correct path
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/claude-bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_token():
    from config import TELEGRAM_BOT_TOKEN
    logger.info(f"Token length: {len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0}")
    logger.info(f"Token format: {'valid' if ':' in TELEGRAM_BOT_TOKEN else 'invalid'}")
    if not TELEGRAM_BOT_TOKEN or ':' not in TELEGRAM_BOT_TOKEN:
        logger.error("Invalid token format!")
        return False
    return True

def main():
    logger.info("DealVault Bot starting...")
    while True:
        try:
            logger.info("Bot is running and polling for updates...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot shutdown")