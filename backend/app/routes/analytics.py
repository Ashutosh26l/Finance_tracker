"""
Analytics API Routes — ML-powered insights.
"""

from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.services.analytics_service import (
    get_overview, get_monthly_trends, get_predictions,
    get_anomalies, get_budget_status, set_budget,
)
from app.schemas.analytics import BudgetCreate

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
async def overview(
    period: int = Query(30, ge=7, le=365, description="Period in days"),
    db=Depends(get_db),
):
    """Get financial overview with income, expenses, savings, and trends."""
    return await get_overview(db, period_days=period)


@router.get("/trends")
async def monthly_trends(
    months: int = Query(6, ge=1, le=24),
    db=Depends(get_db),
):
    """Get monthly income/expense/savings trends."""
    return await get_monthly_trends(db, months=months)


@router.get("/predictions")
async def predictions(
    days: int = Query(30, ge=7, le=90),
    db=Depends(get_db),
):
    """Get ML-powered spending predictions for the next N days."""
    return await get_predictions(db, days=days)


@router.get("/anomalies")
async def anomalies(db=Depends(get_db)):
    """Detect anomalous transactions using Isolation Forest."""
    return await get_anomalies(db)


@router.get("/budget")
async def budget_status(db=Depends(get_db)):
    """Get budget utilization status for the current month."""
    return await get_budget_status(db)


@router.post("/budget")
async def create_budget(
    budget: BudgetCreate,
    db=Depends(get_db),
):
    """Set or update budget for a category."""
    return await set_budget(db, budget.category, budget.limit)
