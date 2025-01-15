from datetime import datetime
import logging
from config import deals, users, Deal

logger = logging.getLogger(__name__)

async def create_deal_group(creator_id: int, deal_type: str, amount: float, terms: str) -> str:
    try:
        deal_id = f"deal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{creator_id}"
        
        deals[deal_id] = Deal(
            id=deal_id,
            creator_id=creator_id,
            deal_type=deal_type,
            amount=amount,
            terms=terms,
            members=[creator_id]
        )
        
        return deal_id
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        return None

async def setup_deal_chat(deal_id: str, group_id: int) -> bool:
    if deal_id not in deals:
        return False
    
    deal = deals[deal_id]
    deal.group_id = group_id
    return True

async def complete_deal(deal_id: str) -> bool:
    if deal_id not in deals:
        return False
    
    deal = deals[deal_id]
    deal.status = 'completed'
    
    for member_id in deal.members:
        if member_id in users:
            users[member_id].completed_deals += 1
            users[member_id].reputation += 1
    
    return True