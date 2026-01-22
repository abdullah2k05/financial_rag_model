from groq import Groq
import os
from typing import Dict, Any, Optional
import json
from dotenv import load_dotenv

load_dotenv(override=True)

class LLMService:
    def __init__(self):
        # Groq SDK automatically looks for GROQ_API_KEY in environment
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("[WARNING] GROQ_API_KEY not found in environment variables.")
        
        self.client = Groq(api_key=self.api_key)
        # Using a supported Groq model
        self.model = "llama-3.1-8b-instant" 

    def classify_intent(self, message: str, history: list) -> Dict[str, Any]:
        """
        Classify user intent into: SEARCH, SUMMARY, INSIGHTS, CHAT.
        Returns JSON.
        """
        system_prompt = """You are the brain of a Financial AI Dashboard.
        Your job is to classify the user's intent and extract relevant parameters.
        
        INTENTS:
        1. SEARCH: User wants to find specific transactions or aggregate sums for a specific entity. 
           - Examples: "Show walmart", "payments to John", "spent at starbucks", "transaction of $50", "how much sent to account X".
           - Extract 'keywords' (list of strict search terms: entities, names, account titles, merchants).
        2. SUMMARY: User wants an overview of general spending or category totals.
           - Examples: "Summarize my spending", "Total income", "How much did I spend on food?".
           - Extract 'category' (optional) and 'time_period' (optional).
        3. INSIGHTS: Analysis and trends.
        4. CHAT: General conversation.

        IMPORTANT: If user asks "how much", "total", or "sum" regarding a PERSON, ACCOUNT, or MERCHANT, classify as SEARCH and extract the name as a keyword.

        OUTPUT JSON FORMAT:
        {
            "intent": "SEARCH" | "SUMMARY" | "INSIGHTS" | "CHAT",
            "parameters": {
                "keywords": ["..."],
                "category": "...",
                "time_period": "..."
            }
        }
        
        Do not explain. Return ONLY JSON.
        """

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add limited history context (last 2 turns) to resolve references
        for role, content in history[-2:]:
             api_role = "assistant" if role == "bot" else role
             messages.append({"role": api_role, "content": content})
             
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"} 
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"[LLM Error] Intent Classification failed: {e}")
            # Fallback to CHAT to be safe
            return {"intent": "CHAT", "parameters": {}}

    def generate_response(self, system_context: str, user_query: str, data_context: str, history: list = []) -> str:
        """
        Generate a natural language response based on financial data and chat history.
        """
        try:
            messages = [{"role": "system", "content": system_context}]
            
            # Inject history
            for role, content in history:
                api_role = "assistant" if role == "bot" else role
                messages.append({"role": api_role, "content": content})
                
            messages.append({"role": "user", "content": f"User Query: {user_query}\n\nData Context:\n{data_context}"})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0, # Enforcing deterministic output
                # top_p=1.0,     # Default
                # seed=42,       # Optional: If supported by provider
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM Error] Generation failed: {e}")
            return "I'm having trouble generating a response right now. Please try again."

# Singleton
llm_service = LLMService()
