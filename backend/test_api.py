from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

print("GROQ_API_KEY:", repr(os.getenv("GROQ_API_KEY")))

try:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    print("API key loaded successfully")
    # Test a simple call
    response = llm.invoke("Hello")
    print("Test response:", response.content)
except Exception as e:
    print("Error:", e)
