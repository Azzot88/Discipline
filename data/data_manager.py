import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.users_file = self.data_dir / "users.json"
        self.deals_file = self.data_dir / "deals.json"
        self.logs_dir = self.data_dir / "logs"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize empty data
        self.users: Dict = {}
        self.deals: Dict = {}
        
        # Load data
        self.load_data()
        
        # Start auto-save
        asyncio.create_task(self.auto_save())
    
    def load_data(self):
        """Load data from JSON files"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            
            if self.deals_file.exists():
                with open(self.deals_file, 'r') as f:
                    self.deals = json.load(f)
                    
            logger.info("Data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self._backup_corrupted_data()
    
    async def save_data(self):
        """Save data to JSON files"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            
            with open(self.deals_file, 'w') as f:
                json.dump(self.deals, f, indent=2)
                
            logger.info("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def _backup_corrupted_data(self):
        """Backup corrupted data files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for file in [self.users_file, self.deals_file]:
            if file.exists():
                backup_file = self.logs_dir / f"{file.stem}_{timestamp}_corrupted{file.suffix}"
                try:
                    file.rename(backup_file)
                    logger.info(f"Corrupted file backed up: {backup_file}")
                except Exception as e:
                    logger.error(f"Error backing up corrupted file: {e}")
    
    async def auto_save(self):
        """Automatically save data every 5 minutes"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            await self.save_data()
    
    # User methods
    def get_user(self, user_id: int) -> Optional[dict]:
        return self.users.get(str(user_id))
    
    def save_user(self, user_id: int, user_data: dict):
        self.users[str(user_id)] = user_data
    
    def delete_user(self, user_id: int):
        self.users.pop(str(user_id), None)
    
    # Deal methods
    def get_deal(self, deal_id: str) -> Optional[dict]:
        return self.deals.get(deal_id)
    
    def save_deal(self, deal_id: str, deal_data: dict):
        self.deals[deal_id] = deal_data
    
    def delete_deal(self, deal_id: str):
        self.deals.pop(deal_id, None)
    
    def get_user_deals(self, user_id: int) -> list:
        return [
            deal for deal in self.deals.values()
            if str(user_id) in [str(deal['creator_id']), *map(str, deal.get('members', []))]
        ] 