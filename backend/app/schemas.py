from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- User ---
class UserCreate(BaseModel):
    username: str
    password: str

# --- Card ---
class CardCreate(BaseModel):
    label: Optional[str] = None
    card_number: str
    holder: Optional[str] = None
    exp: Optional[str] = None
    cvv: Optional[str] = None
    notes: Optional[str] = None

class CardOut(BaseModel):
    id: int
    label: Optional[str]
    masked: str
    holder: Optional[str]
    exp: Optional[str]
    created_at: datetime
    class Config: orm_mode = True

class CardFull(BaseModel):
    id: int
    label: Optional[str]
    card_number: str
    holder: Optional[str]
    exp: Optional[str]
    cvv: Optional[str]
    notes: Optional[str]
    created_at: datetime
    class Config: orm_mode = True

# --- Card Raw ---
class RawCardIn(BaseModel):
    label: Optional[str] = None
    enc_data_b64: str
    nonce_b64: str

class RawCardOut(BaseModel):
    id: int
    label: Optional[str]
    enc_data_b64: str
    nonce_b64: str
    created_at: datetime
    class Config: orm_mode = True

# --- Subscription ---
class SubscriptionBase(BaseModel):
    service_name: str
    cost: float
    currency: str = 'USD'
    billing_cycle: str = 'monthly'
    next_billing_date: Optional[date] = None
    start_date: Optional[date] = None
    notes: Optional[str] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionOut(SubscriptionBase):
    id: int
    created_at: datetime
    class Config: orm_mode = True