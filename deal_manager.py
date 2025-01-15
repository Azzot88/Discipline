from config import bot, users, deals, State
from keyboards import get_chat_keyboard
from datetime import datetime

def create_new_deal(user_id, deal_type, amount, terms, duration, selected_friends):
    try:
        deal_id = f"deal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"
        deals[deal_id] = {
            'creator_id': user_id,
            'amount': amount,
            'terms': terms,
            'duration': duration,
            'status': 'active',
            'type': deal_type,
            'invited_users': list(selected_friends)
        }
        return deal_id
    except Exception as e:
        print(f"Error creating deal: {e}")
        return None

def setup_deal_chat(deal_id, initiator_id, giver_id):
    # Setup chat info
    chat_info = (
        f"🤝 New Deal Chat\n\n"
        f"Deal ID: {deal_id}\n"
        f"Type: {deals[deal_id]['type']}\n"
        f"Amount: {deals[deal_id]['amount']}\n"
        f"Terms: {deals[deal_id]['terms']}\n"
        f"Duration: {deals[deal_id]['duration']} days"
    )
    
    # Setup for both users
    for uid in [initiator_id, giver_id]:
        users[uid]['current_chat'] = {
            'deal_id': deal_id,
            'chat_with': giver_id if uid == initiator_id else initiator_id
        }
        bot.send_message(
            uid,
            chat_info,
            reply_markup=get_chat_keyboard()
        )

def complete_deal(deal_id):
    if deal_id in deals:
        deals[deal_id]['status'] = 'completed'
        initiator_id = deals[deal_id]['creator_id']
        giver_id = deals[deal_id]['giver_id']
        
        for uid in [initiator_id, giver_id]:
            users[uid]['completed_deals'] += 1
            users[uid]['reputation'] += 1
            users[uid]['current_chat'] = None