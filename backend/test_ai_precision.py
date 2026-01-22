import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

async def test_precision_query():
    print("--- AI Precision Query Test ---")
    try:
        from app.services.rag_agent import RagAgent
        from app.services.storage import storage
        from app.models.transaction import Transaction
        from datetime import datetime
        
        # 1. Add some dummy data to ensure our 'account' exists
        dummy_txs = [
            Transaction(
                date=datetime.now(),
                description="Transfer to ACME CORP",
                amount=500.0,
                currency="USD",
                type="debit",
                category="Business",
                balance=5000.0
            ),
            Transaction(
                date=datetime.now(),
                description="Transfer to ACME CORP",
                amount=250.0,
                currency="USD",
                type="debit",
                category="Business",
                balance=4750.0
            ),
            Transaction(
                date=datetime.now(),
                description="Office Supplies",
                amount=50.0,
                currency="USD",
                type="debit",
                category="Supplies",
                balance=4700.0
            )
        ]
        storage.save_transactions(dummy_txs)
        
        agent = RagAgent()
        
        # Simulating the query that was previously failing or inaccurate
        query = "total amount shared to ACME CORP"
        print(f"Query: {query}")
        
        response = await agent.chat(query)
        print("\n--- AI Response ---")
        print(response)
        print("-------------------\n")
        
        # We check if the response contains the sum (500 + 250 = 750)
        if "750" in response or "750.00" in response:
            print("SUCCESS: The agent correctly aggregated the total using keyword search.")
        else:
            print("FAILURE: The agent did not provide the correct total.")

    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_precision_query())
