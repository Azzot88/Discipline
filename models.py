from dataclasses import dataclass
from typing import Optional
from enum import Enum

class DealType(Enum):
    CHARITY = "Charity"
    DEBT = "Debt"
    SERVICE = "Service"
    VENTURE = "Venture"

class DealStatus(Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    COMPLETED = "Completed"

@dataclass
class Deal:
    id: str
    type: DealType
    amount: float
    initiator: str
    savior: Optional[str] = None
    status: DealStatus = DealStatus.PENDING 