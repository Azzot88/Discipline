from dataclasses import dataclass
from enum import Enum

class DealType(str, Enum):
    CHARITY = 'charity'
    DEBT = 'debt'
    SERVICE = 'service'
    VENTURE = 'venture'

class UserState(str, Enum):
    IDLE = 'idle'
    SHARING_CONTACT = 'sharing_contact'
    ENTERING_AMOUNT = 'entering_amount'
    ENTERING_TERMS = 'entering_terms'

@dataclass
class User:
    id: int
    username: str = None
    phone: str = None
    first_name: str = None
    last_name: str = None
    reputation: int = 0
    completed_deals: int = 0
    is_registered: bool = False

@dataclass
class Deal:
    id: str
    creator_id: int
    deal_type: DealType
    amount: float
    terms: str
    status: str = 'active'
    group_id: int = None
    members: list = None

# Storage (can be replaced with database later)
users = {}
deals = {}
user_states = {}
temp_deals = {}
