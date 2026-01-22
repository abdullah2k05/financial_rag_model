import langchain.agents
import langchain_community.agents
import inspect

def find_in_obj(obj, name_to_find, path=""):
    results = []
    for name, member in inspect.getmembers(obj):
        if name == name_to_find:
            results.append(f"{path}.{name}")
        elif inspect.ismodule(member) and member.__name__.startswith("langchain"):
            # Avoid infinite recursion
            pass
    return results

print("Checking langchain.agents:")
print([n for n, _ in inspect.getmembers(langchain.agents) if "agent" in n.lower()])

print("\nChecking langchain_community.agents:")
print([n for n, _ in inspect.getmembers(langchain_community.agents) if "agent" in n.lower()])

try:
    from langchain.agents import create_openai_functions_agent
    print("\nSUCCESS: from langchain.agents import create_openai_functions_agent")
except ImportError:
    print("\nFAILED: from langchain.agents import create_openai_functions_agent")

try:
    from langchain.agents.openai_functions_agent.base import create_openai_functions_agent
    print("SUCCESS: from langchain.agents.openai_functions_agent.base import create_openai_functions_agent")
except ImportError:
    print("FAILED: from langchain.agents.openai_functions_agent.base import create_openai_functions_agent")
