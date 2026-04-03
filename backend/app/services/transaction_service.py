"""
Transaction Service — Business logic for transaction operations.
"""

from datetime import datetime
from bson import ObjectId
from app.ml.categorizer import categorizer
from app.ml.anomaly import anomaly_detector


def serialize_transaction(txn: dict) -> dict:
    """Convert MongoDB document to API response format."""
    return {
        "id": str(txn["_id"]),
        "description": txn.get("description", ""),
        "amount": txn.get("amount", 0),
        "type": txn.get("type", "expense"),
        "category": txn.get("category", "Other"),
        "predicted_category": txn.get("predicted_category"),
        "is_anomaly": txn.get("is_anomaly", False),
        "anomaly_score": txn.get("anomaly_score"),
        "date": txn.get("date", datetime.now()),
        "notes": txn.get("notes"),
        "created_at": txn.get("created_at", datetime.now()),
    }


async def create_transaction(db, data: dict) -> dict:
    """Create a new transaction with ML-powered categorization and anomaly check."""
    now = datetime.now()

    # Auto-categorize if no category provided
    if not data.get("category"):
        prediction = categorizer.predict(data["description"])
        data["category"] = prediction["category"]
        data["predicted_category"] = prediction["category"]
        data["ml_confidence"] = prediction["confidence"]
    else:
        data["predicted_category"] = data["category"]

    # Set defaults
    if not data.get("date"):
        data["date"] = now
    elif isinstance(data["date"], str):
        data["date"] = datetime.fromisoformat(data["date"].replace("Z", "+00:00"))

    data["created_at"] = now
    data["is_anomaly"] = False
    data["anomaly_score"] = None

    # Check for anomalies against historical data
    if data.get("type") == "expense":
        historical = []
        async for txn in db.transactions.find({"type": "expense"}).sort("date", -1).limit(200):
            historical.append(txn)

        if historical:
            anomaly_result = anomaly_detector.check_single(data, historical)
            data["is_anomaly"] = anomaly_result["is_anomaly"]
            data["anomaly_score"] = anomaly_result["anomaly_score"]

    result = await db.transactions.insert_one(data)
    data["_id"] = result.inserted_id

    return serialize_transaction(data)


async def get_transactions(db, skip: int = 0, limit: int = 50,
                           category: str = None, tx_type: str = None,
                           start_date: str = None, end_date: str = None,
                           search: str = None) -> dict:
    """Get transactions with filtering, pagination, and sorting."""
    query = {}

    if category:
        query["category"] = category
    if tx_type:
        query["type"] = tx_type
    if start_date:
        query.setdefault("date", {})["$gte"] = datetime.fromisoformat(start_date)
    if end_date:
        query.setdefault("date", {})["$lte"] = datetime.fromisoformat(end_date)
    if search:
        query["description"] = {"$regex": search, "$options": "i"}

    total = await db.transactions.count_documents(query)
    cursor = db.transactions.find(query).sort("date", -1).skip(skip).limit(limit)

    transactions = []
    async for txn in cursor:
        transactions.append(serialize_transaction(txn))

    return {
        "transactions": transactions,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
    }


async def update_transaction(db, txn_id: str, data: dict) -> dict:
    """Update a transaction. If category is changed, log it for retraining."""
    update_data = {k: v for k, v in data.items() if v is not None}

    if "date" in update_data and isinstance(update_data["date"], str):
        update_data["date"] = datetime.fromisoformat(update_data["date"].replace("Z", "+00:00"))

    update_data["updated_at"] = datetime.now()

    await db.transactions.update_one(
        {"_id": ObjectId(txn_id)},
        {"$set": update_data}
    )

    txn = await db.transactions.find_one({"_id": ObjectId(txn_id)})
    if txn:
        return serialize_transaction(txn)
    return None


async def delete_transaction(db, txn_id: str) -> bool:
    """Delete a transaction by ID."""
    result = await db.transactions.delete_one({"_id": ObjectId(txn_id)})
    return result.deleted_count > 0


async def get_all_categories(db) -> list[str]:
    """Get all unique categories from transactions."""
    categories = await db.transactions.distinct("category")
    return sorted(categories) if categories else []
