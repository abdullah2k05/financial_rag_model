
import asyncio
import sys
import os
from dotenv import load_dotenv

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(override=True)

from app.services.rag_agent import rag_agent

async def test_consistency():
    print("--- Starting Consistency Test ---")
    query = "summarize my spending"
    print(f"Query: '{query}'")
    
    responses = []
    
    for i in range(3):
        print(f"  Run {i+1}...")
        response = await rag_agent.chat(query)
        responses.append(response)
        # Simple wait to ensure no weird race conditions (though not really needed for LLM api calls)
        await asyncio.sleep(1)

    print("\n--- Results ---")
    first_response = responses[0]
    all_match = all(r == first_response for r in responses)
    
    if all_match:
        print("✅ PASS: All 3 responses are identical.")
        # print(f"Response content (truncated): {first_response[:100]}...")
    else:
        print("❌ FAIL: Responses differ.")
        for idx, r in enumerate(responses):
            print(f"  Response {idx+1} length: {len(r)}")
            # print(f"  Preview: {r[:50]}...")
            
    # Also check if response length differs significantly if they aren't exact (sometimes small unique IDs or timestamps might differ, but we want generally exact)
    # Ideally for temp=0 it should be exact byte-for-byte.

if __name__ == "__main__":
    asyncio.run(test_consistency())
