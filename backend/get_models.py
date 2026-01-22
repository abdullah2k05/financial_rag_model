import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)
client = Groq()

with open("available_models.txt", "w") as f:
    for m in client.models.list().data:
        f.write(f"{m.id}\n")
print("Saved to available_models.txt")
