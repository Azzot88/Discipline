from datetime import datetime
import logging
from typing import Optional
from config import Deal, DealType

logger = logging.getLogger(__name__)

class DealManager:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    async def create_deal_group(self, creator_id: int, deal_type: str, amount: float, terms: str) -> Optional[str]:
        try:
            deal_id = f"deal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{creator_id}"
            
            deal = Deal(
                id=deal_id,
                creator_id=creator_id,
                deal_type=DealType(deal_type),
                amount=amount,
                terms=terms,
                members=[creator_id]
            )
            
            self.data_manager.save_deal(deal_id, deal.to_dict())
            return deal_id
            
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            return None

    async def setup_deal_chat(self, deal_id: str, group_id: int) -> bool:
        deal_data = self.data_manager.get_deal(deal_id)
        if not deal_data:
            return False
        
        deal = Deal.from_dict(deal_data)
        deal.group_id = group_id
        self.data_manager.save_deal(deal_id, deal.to_dict())
        return True

    async def complete_deal(self, deal_id: str) -> bool:
        deal_data = self.data_manager.get_deal(deal_id)
        if not deal_data:
            return False
        
        deal = Deal.from_dict(deal_data)
        deal.status = 'completed'
        self.data_manager.save_deal(deal_id, deal.to_dict())
        
        for member_id in deal.members:
            user_data = self.data_manager.get_user(member_id)
            if user_data:
                user = User.from_dict(user_data)
                user.completed_deals += 1
                user.reputation += 1
                self.data_manager.save_user(member_id, user.to_dict())
        
        return True