import asyncio
from app.services.rag_agent import rag_agent
from app.services.storage import storage
from app.models.transaction import Transaction
from datetime import datetime

async def test_simple():
    """Simple test to verify chatbot accuracy"""
    # Clear previous data
    storage.clear_all()
    from app.services.vector_store import vector_store
    vector_store.clear()

    # Add test transactions
    txs = [
        Transaction(date=datetime.now(), description='Walmart Groceries', amount=100.0, currency='USD', type='debit', category='Groceries', balance=900.0),
        Transaction(date=datetime.now(), description='Shell Gas', amount=50.0, currency='USD', type='debit', category='Transportation', balance=850.0),
        Transaction(date=datetime.now(), description='Salary', amount=3000.0, currency='USD', type='credit', category='Income', balance=3850.0),
    ]
    storage.save_transactions(txs)
    vector_store.index_transactions(txs)

    # Test query
    query = "How much did I spend on groceries?"
    print(f"\nQuery: {query}")
    response = await rag_agent.chat(query)
    print(f"Response: {response}\n")
    
    # Should see $100.00 in the response
    if "$100" in response or "100.00" in response:
        print("✓ TEST PASSED: Correct grocery amount found")
    else:
        print("✗ TEST FAILED: Expected $100.00 for groceries")

if __name__ == "__main__":
    asyncio.run(test_simple())
