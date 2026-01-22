import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

# Mock Transaction class
class MockTransaction:
    def __init__(self, description, amount, type, date_str, category=None):
        self.description = description
        self.amount = amount
        self.type = type
        self.date = datetime.now() # Simplified date
        self.currency = "USD"
        self.category = category
        self.raw_data = {}

# Mock transactions
mock_txs = [
    MockTransaction("Walmart", 50.0, "debit", "2023-01-01", "Groceries"),
    MockTransaction("Salary", 2000.0, "credit", "2023-01-01", "Income"),
    MockTransaction("Netflix", 15.0, "debit", "2023-01-02", "Entertainment"),
]

# Patch storage before importing rag_agent
with patch("app.services.storage.storage") as mock_storage:
    mock_storage.get_all_transactions.return_value = mock_txs
    
    # Import rag_agent (it will use the mocked storage if we patched it correctly, 
    # but rag_agent imports storage at module level, so we might need to patch where it is used or imported)
    # Actually, since rag_agent imports 'storage' instance, we can patch 'app.services.rag_agent.storage'
    
    from app.services.rag_agent import rag_agent
    
    # We need to re-apply the patch to the storage instance inside rag_agent because it was already imported
    rag_agent.storage = mock_storage # This might not work if rag_agent.py uses 'storage' from global scope of its module.
    # Let's check rag_agent.py imports: "from app.services.storage import storage"
    # So we need to patch 'app.services.rag_agent.storage'

    # Better way: Modify the storage reference in rag_agent module
    import app.services.rag_agent
    app.services.rag_agent.storage = mock_storage

    async def run_test():
        print("--- Test 1: 'summarize all of my spending' ---")
        response = await rag_agent.chat("summarize all of my spending")
        print(f"Response:\n{response}\n")
        
        print("--- Test 2: 'summarize spending' ---")
        response = await rag_agent.chat("summarize spending")
        print(f"Response:\n{response}\n")

    if __name__ == "__main__":
        asyncio.run(run_test())
