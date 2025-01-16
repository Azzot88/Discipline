from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import asdict

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
class UserStatistics:
    total_deals_created: int = 0
    total_deals_participated: int = 0
    total_amount_handled: float = 0.0
    successful_deals: int = 0
    failed_deals: int = 0

@dataclass
class UserSettings:
    notifications: bool = True
    language: str = 'en'

@dataclass
class User:
    id: int
    username: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    reputation: int = 0
    completed_deals: int = 0
    active_deals: List[str] = None
    is_registered: bool = False
    joined_date: Optional[str] = None
    last_active: Optional[str] = None
    settings: Optional[UserSettings] = None
    statistics: Optional[UserStatistics] = None

    def __post_init__(self):
        if self.active_deals is None:
            self.active_deals = []
        if self.settings is None:
            self.settings = UserSettings()
        if self.statistics is None:
            self.statistics = UserStatistics()
        if self.joined_date is None:
            self.joined_date = datetime.now().isoformat()
        self.last_active = datetime.now().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'phone': self.phone,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'reputation': self.reputation,
            'completed_deals': self.completed_deals,
            'active_deals': self.active_deals,
            'is_registered': self.is_registered,
            'joined_date': self.joined_date,
            'last_active': self.last_active,
            'settings': asdict(self.settings),
            'statistics': asdict(self.statistics)
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

@dataclass
class DealParticipant:
    role: str
    joined_at: str
    status: str = 'active'

@dataclass
class DealMetadata:
    currency: str = 'USD'
    payment_method: Optional[str] = None
    deadline: Optional[str] = None
    attachments: List[str] = None

@dataclass
class DealHistoryEntry:
    timestamp: str
    action: str
    user_id: int

@dataclass
class Deal:
    id: str
    creator_id: int
    deal_type: DealType
    amount: float
    terms: str
    status: str = 'active'
    group_id: Optional[int] = None
    members: List[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completion_date: Optional[str] = None
    history: List[DealHistoryEntry] = None
    metadata: Optional[DealMetadata] = None
    participants: Dict[int, DealParticipant] = None

    def __post_init__(self):
        if self.members is None:
            self.members = []
        if self.history is None:
            self.history = []
        if self.metadata is None:
            self.metadata = DealMetadata()
        if self.participants is None:
            self.participants = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'creator_id': self.creator_id,
            'deal_type': self.deal_type,
            'amount': self.amount,
            'terms': self.terms,
            'status': self.status,
            'group_id': self.group_id,
            'members': self.members,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completion_date': self.completion_date,
            'history': [asdict(h) for h in self.history],
            'metadata': asdict(self.metadata),
            'participants': {
                str(k): asdict(v) for k, v in self.participants.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
