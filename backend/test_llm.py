import os
from groq import Groq
from dotenv import load_dotenv

# Debugging: Read file directly
with open(".env", "r") as f:
    print(f"DEBUG - .env content:\n{f.read()}")

load_dotenv(".env", override=True)
api_key = os.getenv("GROQ_API_KEY") 
if not api_key:
    # Fallback to OPENROUTER_API_KEY if user hasn't cleaned up env
    api_key = os.getenv("OPENROUTER_API_KEY") 

print(f"Key loaded: {bool(api_key)}")
if api_key:
    print(f"Key preview: {api_key[:10]}...")

client = Groq(api_key=api_key)

try:
    print("Testing Groq connection with llama-3.1-8b-instant...")
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95
    )
    print("Success:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
