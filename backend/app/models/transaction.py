from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Transaction(BaseModel):
    date: datetime
    description: str
    amount: float
    currency: str = "USD"
    type: str  # "credit" or "debit"
    balance: Optional[float] = None
    category: Optional[str] = None
    raw_data: Optional[dict] = None  # To store original row data for debugging

class StatementMetadata(BaseModel):
    bank_name: Optional[str] = None
    account_id: Optional[str] = None
    currency: Optional[str] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
