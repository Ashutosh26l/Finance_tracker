"""
Category API Routes
"""

from fastapi import APIRouter, Depends
from app.database import get_db
from app.services.transaction_service import get_all_categories
from app.schemas.transaction import CATEGORIES

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("")
async def list_categories(db=Depends(get_db)):
    """Get all available categories (predefined + user-created)."""
    db_categories = await get_all_categories(db)
    all_cats = list(set(CATEGORIES + db_categories))
    return {"categories": sorted(all_cats)}


@router.get("/summary")
async def category_summary(db=Depends(get_db)):
    """Get spending summary per category for the current month."""
    from datetime import datetime
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    pipeline = [
        {"$match": {"type": "expense", "date": {"$gte": month_start}}},
        {"$group": {
            "_id": "$category",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1},
            "avg_amount": {"$avg": "$amount"},
        }},
        {"$sort": {"total": -1}},
    ]

    results = []
    async for doc in db.transactions.aggregate(pipeline):
        results.append({
            "category": doc["_id"],
            "total": round(doc["total"], 2),
            "count": doc["count"],
            "avg_amount": round(doc["avg_amount"], 2),
        })

    return {"categories": results}
