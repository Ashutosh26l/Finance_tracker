from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Bills & Utilities",
    "Entertainment",
    "Health & Fitness",
    "Education",
    "Travel",
    "Subscriptions",
    "Groceries",
    "Rent & Housing",
    "Income",
    "Other"
]


class TransactionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    type: TransactionType = TransactionType.EXPENSE
    category: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Starbucks Coffee",
                "amount": 5.40,
                "type": "expense",
                "category": "Food & Dining",
                "date": "2026-03-15T10:30:00",
                "notes": "Morning latte"
            }
        }


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    description: str
    amount: float
    type: TransactionType
    category: str
    predicted_category: Optional[str] = None
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None
    date: datetime
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                "description": "Starbucks Coffee",
                "amount": 5.40,
                "type": "expense",
                "category": "Food & Dining",
                "predicted_category": "Food & Dining",
                "is_anomaly": False,
                "anomaly_score": -0.15,
                "date": "2026-03-15T10:30:00",
                "notes": "Morning latte",
                "created_at": "2026-03-15T10:35:00"
            }
        }


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    page: int
    per_page: int


class CSVUploadResponse(BaseModel):
    imported: int
    failed: int
    errors: list[str] = []
