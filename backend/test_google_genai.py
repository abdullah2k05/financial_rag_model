from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

print("GOOGLE_API_KEY:", repr(os.getenv("GOOGLE_API_KEY")))

# First, list available models
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
try:
    models = genai.list_models()
    print("Available models:")
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
except Exception as e:
    print("Error listing models:", e)

try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)
    print("API key loaded successfully")
    # Test a simple call
    response = llm.invoke("Hello")
    print("Test response:", response.content)
except Exception as e:
    print("Error:", e)
