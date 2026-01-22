import traceback
from app.services.rag_agent import rag_agent

try:
    print("Initializing Agent...")
    print(f"Agent: {rag_agent.agent}")
    print("SUCCESS")
except TypeError:
    traceback.print_exc()
except Exception:
    traceback.print_exc()
