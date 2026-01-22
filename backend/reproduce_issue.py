import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables (for OpenAI/OpenRouter key)
load_dotenv(".env", override=True) 

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
    
    # Import rag_agent 
    from app.services.rag_agent import rag_agent
    
    # Needs to patch 'app.services.rag_agent.storage' or 'app.services.storage.storage' in the correct namespace
    # Since rag_agent does 'from app.services.storage import storage', we target that
    import app.services.rag_agent
    app.services.rag_agent.storage = mock_storage

    async def run_test():
        print("--- Test 1: 'summarize all of my spending' ---")
        try:
            response = await rag_agent.chat("summarize all of my spending")
            print(f"Response:\n{response}\n")
        except Exception as e:
            print(f"Test 1 Error: {e}")
        
        print("--- Test 2: 'summarize spending' ---")
        try:
            response = await rag_agent.chat("summarize spending")
            print(f"Response:\n{response}\n")
        except Exception as e:
            print(f"Test 2 Error: {e}")

    if __name__ == "__main__":
        asyncio.run(run_test())
