import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env")
api_key = os.getenv("OPENROUTER_API_KEY")

print(f"Key loaded: {bool(api_key)}")
if api_key:
    print(f"Key preview: {api_key[:10]}...")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

try:
    print("Testing connection...")
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct:free",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7
    )
    print("Success:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
    # Inspect raw response if possible
