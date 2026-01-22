import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
info = os.getenv("GOOGLE_API_KEY")
print(f"Key starts with: {info[:10]}..." if info else "No key found")

genai.configure(api_key=info)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
