"""
Analytics Service — Business logic for analytics and ML insights.
"""

from datetime import datetime, timedelta
from app.ml.predictor import predictor
from app.ml.anomaly import anomaly_detector
from app.ml.categorizer import categorizer
import numpy as np


async def get_overview(db, period_days: int = 30) -> dict:
    """Get financial overview with income, expenses, savings, and trends."""
    now = datetime.now()
    period_start = now - timedelta(days=period_days)
    prev_period_start = period_start - timedelta(days=period_days)

    # Current period
    current_txns = []
    async for txn in db.transactions.find({"date": {"$gte": period_start}}):
        current_txns.append(txn)

    # Previous period (for trends)
    prev_txns = []
    async for txn in db.transactions.find({
        "date": {"$gte": prev_period_start, "$lt": period_start}
    }):
        prev_txns.append(txn)

    # Calculate current period stats
    total_income = sum(t["amount"] for t in current_txns if t.get("type") == "income")
    total_expenses = sum(t["amount"] for t in current_txns if t.get("type") == "expense")
    net_savings = total_income - total_expenses

    # Previous period stats for trends
    prev_income = sum(t["amount"] for t in prev_txns if t.get("type") == "income")
    prev_expenses = sum(t["amount"] for t in prev_txns if t.get("type") == "expense")

    income_trend = ((total_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
    expense_trend = ((total_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0

    # Category breakdown
    categories = {}
    expense_txns = [t for t in current_txns if t.get("type") == "expense"]
    for txn in expense_txns:
        cat = txn.get("category", "Other")
        if cat not in categories:
            categories[cat] = {"total": 0, "count": 0}
        categories[cat]["total"] += txn["amount"]
        categories[cat]["count"] += 1

    category_list = []
    for cat, data in sorted(categories.items(), key=lambda x: x[1]["total"], reverse=True):
        category_list.append({
            "category": cat,
            "total": round(data["total"], 2),
            "count": data["count"],
            "percentage": round(data["total"] / total_expenses * 100, 1) if total_expenses > 0 else 0,
        })

    top_category = category_list[0]["category"] if category_list else None
    days_in_period = max(period_days, 1)
    avg_daily = total_expenses / days_in_period

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_savings": round(net_savings, 2),
        "transaction_count": len(current_txns),
        "avg_daily_spending": round(avg_daily, 2),
        "top_category": top_category,
        "income_trend": round(income_trend, 1),
        "expense_trend": round(expense_trend, 1),
        "categories": category_list,
    }


async def get_monthly_trends(db, months: int = 6) -> list[dict]:
    """Get monthly income/expense/savings trends."""
    now = datetime.now()
    trends = []

    for i in range(months - 1, -1, -1):
        # Calculate month boundaries
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1

        # Start and end of month
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)

        # Query transactions in this month
        txns = []
        async for txn in db.transactions.find({
            "date": {"$gte": month_start, "$lt": month_end}
        }):
            txns.append(txn)

        income = sum(t["amount"] for t in txns if t.get("type") == "income")
        expenses = sum(t["amount"] for t in txns if t.get("type") == "expense")

        trends.append({
            "month": month_start.strftime("%b %Y"),
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "savings": round(income - expenses, 2),
        })

    return trends


async def get_predictions(db, days: int = 30) -> dict:
    """Get spending predictions using the ML predictor."""
    # Fetch historical transactions for training
    transactions = []
    async for txn in db.transactions.find().sort("date", -1).limit(500):
        transactions.append({
            "date": txn.get("date", datetime.now()),
            "amount": txn.get("amount", 0),
            "type": txn.get("type", "expense"),
            "category": txn.get("category", "Other"),
        })

    result = predictor.predict(days=days, transactions=transactions)
    if not categorizer.is_trained:
        categorizer.load_model()
    result["categorizer_accuracy"] = round(float(categorizer.accuracy), 4) if categorizer.accuracy else 0.0
    return result


async def get_anomalies(db) -> dict:
    """Detect anomalous transactions using the ML anomaly detector."""
    transactions = []
    async for txn in db.transactions.find({"type": "expense"}).sort("date", -1).limit(300):
        transactions.append(txn)

    anomalies = anomaly_detector.detect(transactions)

    return {
        "anomalies": anomalies,
        "total_flagged": len(anomalies),
        "detection_model": "Isolation Forest",
    }


async def get_budget_status(db) -> dict:
    """Get budget utilization status for the current month."""
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    # Get budgets
    budgets_data = {}
    async for budget in db.budgets.find():
        budgets_data[budget["category"]] = budget.get("limit", 0)

    # Get current month spending per category
    spending = {}
    async for txn in db.transactions.find({
        "type": "expense",
        "date": {"$gte": month_start}
    }):
        cat = txn.get("category", "Other")
        spending[cat] = spending.get(cat, 0) + txn.get("amount", 0)

    # Build budget items
    budget_items = []
    total_budget = 0
    total_spent = 0

    all_categories = set(list(budgets_data.keys()) + list(spending.keys()))

    for cat in sorted(all_categories):
        limit = budgets_data.get(cat, 0)
        spent = round(spending.get(cat, 0), 2)
        remaining = round(limit - spent, 2) if limit > 0 else 0
        utilization = round((spent / limit * 100), 1) if limit > 0 else 0

        if utilization > 100:
            status = "over_budget"
        elif utilization > 80:
            status = "warning"
        else:
            status = "on_track"

        budget_items.append({
            "category": cat,
            "budget_limit": limit,
            "spent": spent,
            "remaining": remaining,
            "utilization": utilization,
            "status": status,
        })

        total_budget += limit
        total_spent += spent

    overall_utilization = round((total_spent / total_budget * 100), 1) if total_budget > 0 else 0

    return {
        "budgets": budget_items,
        "total_budget": round(total_budget, 2),
        "total_spent": round(total_spent, 2),
        "overall_utilization": overall_utilization,
    }


async def set_budget(db, category: str, limit: float) -> dict:
    """Set or update budget for a category."""
    await db.budgets.update_one(
        {"category": category},
        {"$set": {"category": category, "limit": limit, "updated_at": datetime.now()}},
        upsert=True,
    )
    return {"category": category, "limit": limit}
