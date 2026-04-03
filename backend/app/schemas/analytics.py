from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int
    percentage: float


class OverviewResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    transaction_count: int
    avg_daily_spending: float
    top_category: Optional[str] = None
    income_trend: float = 0.0  # percentage change from previous period
    expense_trend: float = 0.0
    categories: list[CategorySummary] = []


class PredictionPoint(BaseModel):
    date: str
    predicted_amount: float
    lower_bound: float
    upper_bound: float


class PredictionResponse(BaseModel):
    predictions: list[PredictionPoint]
    total_predicted: float
    avg_daily_predicted: float
    model_confidence: float


class AnomalyTransaction(BaseModel):
    id: str
    description: str
    amount: float
    category: str
    date: datetime
    anomaly_score: float
    reason: str


class AnomalyResponse(BaseModel):
    anomalies: list[AnomalyTransaction]
    total_flagged: int
    detection_model: str = "Isolation Forest"


class BudgetItem(BaseModel):
    category: str
    budget_limit: float
    spent: float
    remaining: float
    utilization: float  # percentage
    status: str  # "on_track", "warning", "over_budget"


class BudgetCreate(BaseModel):
    category: str
    limit: float = 0.0


class BudgetResponse(BaseModel):
    budgets: list[BudgetItem]
    total_budget: float
    total_spent: float
    overall_utilization: float


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expenses: float
    savings: float
