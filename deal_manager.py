from config import bot, users, deals, State
from keyboards import get_chat_keyboard
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_deal_group(creator_id, deal_type, amount, terms):
    try:
        # Validate inputs
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if not terms.strip():
            raise ValueError("Terms cannot be empty")
            
        # Check user's active deals
        active_deals = sum(1 for d in deals.values() 
                         if d['creator_id'] == creator_id and d['status'] == 'active')
        if active_deals >= 5:  # Limit active deals
            raise ValueError("You have too many active deals")
            
        # Generate unique deal ID
        deal_id = f"deal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{creator_id}"
        
        # Create deal record
        deals[deal_id] = {
            'creator_id': creator_id,
            'type': deal_type,
            'amount': amount,
            'terms': terms,
            'status': 'active',
            'created_at': datetime.now(),
            'members': [creator_id],
            'group_id': None  # Will be set when group is created
        }
        
        # Create group invite link message
        instructions = (
            f"🤝 New Deal Created!\n\n"
            f"Type: {deal_type}\n"
            f"Amount: {amount}\n"
            f"Terms: {terms}\n\n"
            f"Please create a group and add this bot as admin.\n"
            f"Then use /setup_deal_{deal_id} in the group."
        )
        
        bot.send_message(creator_id, instructions)
        return deal_id
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating deal group: {e}")
        return None

def setup_deal_chat(deal_id, group_id):
    if deal_id not in deals:
        return False
        
    deal = deals[deal_id]
    deal['group_id'] = group_id
    
    # Send deal info to group
    chat_info = (
        f"🤝 Deal Setup Complete!\n\n"
        f"Deal ID: {deal_id}\n"
        f"Type: {deal['type']}\n"
        f"Amount: {deal['amount']}\n"
        f"Terms: {deal['terms']}\n\n"
        f"All members please share your contact information if you haven't already."
    )
    
    bot.send_message(group_id, chat_info)
    return True

def complete_deal(deal_id):
    if deal_id in deals:
        deal = deals[deal_id]
        deal['status'] = 'completed'
        
        # Update reputation for all members
        for member_id in deal['members']:
            users[member_id]['completed_deals'] += 1
            users[member_id]['reputation'] += 1
        
        # Notify group
        if deal['group_id']:
            bot.send_message(
                deal['group_id'],
                "🎉 Deal has been completed! Everyone's reputation has been updated."
            )

def check_deal_timeouts():
    current_time = datetime.now()
    for deal_id, deal in deals.items():
        if deal['status'] == 'active':
            time_diff = current_time - deal['created_at']
            if time_diff.days > 30:  # 30 days timeout
                deal['status'] = 'expired'
                if deal['group_id']:
                    bot.send_message(
                        deal['group_id'],
                        "⚠️ This deal has expired due to inactivity."
                    )