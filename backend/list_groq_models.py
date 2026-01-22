import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(".env", override=True)
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

try:
    print("Listing models...")
    models = client.models.list()
    for m in models.data:
        print(f"- {m.id}")
except Exception as e:
    print(f"Error: {e}")
