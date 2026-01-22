import os
import langchain

package_path = os.path.dirname(langchain.__file__)
print(f"Searching in: {package_path}")

found = False
for root, dirs, files in os.walk(package_path):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "class AgentExecutor" in content:
                        print(f"Found AgentExecutor in: {path}")
                        found = True
            except:
                pass
if not found:
    print("AgentExecutor not found in langchain package.")
