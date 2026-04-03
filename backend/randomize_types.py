import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient

async def force_incomes():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.finance_tracker
    collection = db.transactions

    cursor = collection.find({})
    transactions = await cursor.to_list(length=1000)

    if not transactions:
        print("No transactions found.")
        return

    random.shuffle(transactions)
    income_count = 0
    target = min(15, len(transactions))

    for txn in transactions:
        if income_count >= target:
            # Set the rest back to expense just in case previous runs messed them up
            await collection.update_one({"_id": txn["_id"]}, {"$set": {"type": "expense"}})
            continue
            
        await collection.update_one(
            {"_id": txn["_id"]},
            {"$set": {"type": "income", "category": "Income"}}
        )
        income_count += 1

    print(f"Successfully guaranteed {income_count} transactions as Income!")

if __name__ == "__main__":
    asyncio.run(force_incomes())
