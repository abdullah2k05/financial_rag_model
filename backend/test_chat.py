import asyncio
from app.services.rag_agent import rag_agent
from app.services.storage import storage
from app.models.transaction import Transaction
from datetime import datetime

async def main():
    # Clear previous data
    storage.clear_all()
    from app.services.vector_store import vector_store
    vector_store.clear()

    # Add comprehensive test data
    txs = [
        # Grocery transactions
        Transaction(date=datetime.now(), description='Grocery shopping at Walmart', amount=150.0, currency='USD', type='debit', category='Groceries', balance=1000.0),
        Transaction(date=datetime.now(), description='Walmart groceries', amount=75.0, currency='USD', type='debit', category='Groceries', balance=850.0),
        Transaction(date=datetime.now(), description='Target grocery shopping', amount=100.0, currency='USD', type='debit', category='Groceries', balance=750.0),
        
        # Gas/Transportation
        Transaction(date=datetime.now(), description='Shell Gas Station', amount=50.0, currency='USD', type='debit', category='Transportation', balance=700.0),
        Transaction(date=datetime.now(), description='Uber Ride', amount=25.0, currency='USD', type='debit', category='Transportation', balance=675.0),
        
        # Entertainment  
        Transaction(date=datetime.now(), description='Netflix Subscription', amount=15.0, currency='USD', type='debit', category='Entertainment', balance=660.0),
        Transaction(date=datetime.now(), description='AMC Movie Theater', amount=30.0, currency='USD', type='debit', category='Entertainment', balance=630.0),
        
        # Income
        Transaction(date=datetime.now(), description='Salary from ACME Corp', amount=3000.0, currency='USD', type='credit', category='Income', balance=3630.0),
        Transaction(date=datetime.now(), description='Freelance payment from Client X', amount=500.0, currency='USD', type='credit', category='Income', balance=4130.0),
    ]
    storage.save_transactions(txs)
    vector_store.index_transactions(txs)

    print("=" * 80)
    print("FINANCIAL AI CHATBOT TEST SUITE")
    print("=" * 80)
    
    # Test cases
    test_queries = [
        "How much did I spend on groceries?",
        "What did I spend at Walmart?",
        "What is my total spending?",
        "How much income did I receive?",
        "Show me entertainment expenses",
        "What's my net balance?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")
        
        response = await rag_agent.chat(query, chat_history=[])
        print(f"\nRESPONSE:\n{response}")
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())