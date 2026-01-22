from fastapi import APIRouter
from app.services.storage import storage
from app.services.analytics import Analytics
from app.services.vector_store import vector_store

router = APIRouter()

@router.get("/summary")
async def get_summary():
    transactions = storage.get_all_transactions()
    if not transactions:
        return {
            "total_income": 0,
            "total_expense": 0,
            "net_balance": 0,
            "transaction_count": 0
        }
    return Analytics.calculate_summary(transactions)

@router.get("/spending")
async def get_spending_breakdown():
    transactions = storage.get_all_transactions()
    return Analytics.calculate_category_breakdown(transactions)

@router.get("/trends")
async def get_monthly_trends():
    transactions = storage.get_all_transactions()
    return Analytics.calculate_monthly_trends(transactions)

@router.get("/merchants")
async def get_top_merchants():
    transactions = storage.get_all_transactions()
    return Analytics.calculate_top_merchants(transactions)

@router.post("/reset")
async def reset_data():
    """Clear all stored transactions and embeddings, returning an empty summary."""
    try:
        storage.clear_all()
    except Exception as e:
        print("[ERROR] Failed to clear transaction storage:", repr(e))
    try:
        vector_store.clear()
    except Exception as e:
        print("[ERROR] Failed to clear vector store:", repr(e))

    return {
        "total_income": 0,
        "total_expense": 0,
        "net_balance": 0,
        "transaction_count": 0,
    }
