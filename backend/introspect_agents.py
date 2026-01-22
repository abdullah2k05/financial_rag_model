import langchain.agents
import inspect
import os

print(f"langchain.agents file: {langchain.agents.__file__}")
print(f"Starting directory: {os.path.dirname(langchain.agents.__file__)}")

print("Available names in langchain.agents:")
for name in dir(langchain.agents):
    print(name)

try:
    from langchain.agents import AgentExecutor
    print("SUCCESS: Imported AgentExecutor from langchain.agents")
except ImportError as e:
    print(f"FAILED: {e}")

# Check recursively
try:
    import langchain.agents.agent
    print("langchain.agents.agent exists")
except ImportError:
    print("langchain.agents.agent DOES NOT exist")

