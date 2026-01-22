from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import json

from app.services.storage import storage
from app.services.analytics import Analytics


class RagAgent:
    """Context-aware RAG Agent for premium fintech dashboard."""
    
    def __init__(self):
        print("RagAgent: Starting __init__ (Context-Aware Mode)")
        self.currency_symbols = {
            "PKR": "Rs.", "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "AED": "DH"
        }
        print("RagAgent: __init__ finished")

    def _get_active_currency(self) -> str:
        txs = storage.get_all_transactions()
        if txs:
            code = txs[0].currency or "USD"
            return self.currency_symbols.get(code.upper(), code)
        return "$"
    
    def _get_currency_code(self) -> str:
        txs = storage.get_all_transactions()
        if txs:
            return txs[0].currency or "USD"
        return "USD"

    def _get_date_range(self, txs) -> tuple:
        if not txs:
            return None, None
        dates = sorted([t.date for t in txs])
        return dates[0], dates[-1]

    # ==========================================
    # CONTEXT 1: HOME_PAGE - KPI JSON
    # ==========================================
    def get_home_kpis(self) -> Dict[str, Any]:
        """Generate KPI metrics for home page cards. Returns JSON."""
        txs = storage.get_all_transactions()
        
        if not txs:
            return {
                "net_balance": 0,
                "average_monthly_income": 0,
                "average_monthly_spending": 0,
                "currency": "USD"
            }
        
        # Calculate monthly aggregates
        trends = Analytics.calculate_monthly_trends(txs)
        summ = Analytics.calculate_summary(txs)
        
        num_months = len(trends) if trends else 1
        avg_income = summ['total_income'] / num_months
        avg_spending = summ['total_expense'] / num_months
        
        return {
            "net_balance": round(summ['net_balance'], 2),
            "average_monthly_income": round(avg_income, 2),
            "average_monthly_spending": round(avg_spending, 2),
            "currency": self._get_currency_code()
        }

    # ==========================================
    # CONTEXT 2: TRANSACTIONS_PAGE - Snapshot
    # ==========================================
    def get_transactions_snapshot(self) -> str:
        """Generate Financial Snapshot for Transactions page. Returns Markdown."""
        txs = storage.get_all_transactions()
        symbol = self._get_active_currency()
        
        if not txs:
            return "## Financial Snapshot\n\n**No transaction data available.**\n\nUpload a bank statement to see your financial overview."
        
        summ = Analytics.calculate_summary(txs)
        cats = Analytics.calculate_category_breakdown(txs)
        trends = Analytics.calculate_monthly_trends(txs)
        
        # Date range
        date_from, date_to = self._get_date_range(txs)
        date_range = f"{date_from.strftime('%b %d, %Y')} → {date_to.strftime('%b %d, %Y')}" if date_from else "N/A"
        
        # Transaction Analysis
        debits = [t for t in txs if t.type == "debit"]
        credits = [t for t in txs if t.type == "credit"]
        
        highest_debit = max(debits, key=lambda x: x.amount, default=None)
        
        # Top Sender (Income Source)
        sender_map = {}
        for c in credits:
            sender_map[c.description] = sender_map.get(c.description, 0) + c.amount
        top_sender = max(sender_map.items(), key=lambda x: x[1]) if sender_map else ("Unknown", 0)
        
        # Most Frequent Merchant
        merch_map = {}
        for d in debits:
            merch_map[d.description] = merch_map.get(d.description, 0) + 1
        top_freq_merch = max(merch_map.items(), key=lambda x: x[1]) if merch_map else ("None", 0)

        # Top spending category
        top_cat = max(cats.items(), key=lambda x: x[1], default=("N/A", 0)) if cats else ("N/A", 0)
        top_cat_pct = (top_cat[1] / summ['total_expense'] * 100) if summ['total_expense'] > 0 else 0
        
        # Cash flow trend analysis
        trend_list = list(sorted(trends.items()))
        if len(trend_list) >= 2:
            last_net = trend_list[-1][1]['income'] - trend_list[-1][1]['expense']
            prev_net = trend_list[-2][1]['income'] - trend_list[-2][1]['expense']
            if last_net > prev_net:
                trend_direction = "Upward"
            elif last_net < prev_net:
                trend_direction = "Downward"
            else:
                trend_direction = "Stable"
        else:
            trend_direction = "Analyzing..."
        
        # Generate Data-Driven Insights
        insights = []
        if top_sender[1] > 0:
            insights.append(f"Top Sender: **{top_sender[0]}** contributed **{symbol}{top_sender[1]:,.0f}** to income")
        if top_freq_merch[1] > 1:
            insights.append(f"Most Frequent: **{top_freq_merch[0]}** seen **{top_freq_merch[1]} times**")
        if highest_debit:
            insights.append(f"Max Spend: **{symbol}{highest_debit.amount:,.0f}** on {highest_debit.category or 'General'}")

        # Construct Executive Report
        snapshot = f"""## Financial Snapshot

### Overall Position
Net Balance
**{symbol}{summ['net_balance']:,.2f}**

Total Income
**{symbol}{summ['total_income']:,.2f}**

Total Spending
**{symbol}{summ['total_expense']:,.2f}**

---

### Key Highlights
"""
        if highest_debit:
            snapshot += f"Largest Transaction\n**{symbol}{highest_debit.amount:,.0f}** · {highest_debit.category or 'Uncategorized'} · {highest_debit.date.strftime('%d %b')}\n\n"
        snapshot += f"Top Spending Category\n**{top_cat[0]}** ({top_cat_pct:.0f}% of total spending)\n"
        
        snapshot += f"""
---

### Cash Flow Trend
**{trend_direction}** — Based on {len(trends)} months of data

---

### Insights
"""
        for insight in insights:
            snapshot += f"• {insight}\n"
        
        return snapshot

    # ==========================================
    # CONTEXT 2.5: MEMORY & REFERENCE RESOLUTION
    # ==========================================
    def _resolve_references(self, message: str, chat_history: List) -> str:
        """Resolve 'it', 'this account', etc. from chat history (Strict Rules)."""
        if not chat_history:
            return message
            
        # Target keywords for resolution
        refs = ["it", "this account", "that account", "that transaction", "previous result", "same period"]
        msg_l = message.lower()
        
        has_ref = any(r in msg_l for r in refs)
        if not has_ref:
            return message
            
        # Scan backward for the last successful search result
        # Format used in _format_search_response is "## 🔍 Result: [Subject]" or "**[Subject]** Summary"
        last_subject = None
        for turn in reversed(chat_history):
            content = turn.get("content", "")
            # Pattern matching our specific response formats
            match = re.search(r'\## 🔍 Result: (.*?)\n', content)
            if not match:
                match = re.search(r'\*\*(.*?)\*\*\sSummary:', content)
            
            if match:
                last_subject = match.group(1).strip()
                break
        
        if last_subject:
            # Replace references with the explicit subject
            new_msg = message
            for r in refs:
                # Use regex for word-boundary replacement
                new_msg = re.sub(rf'\b{r}\b', last_subject, new_msg, flags=re.IGNORECASE)
            return new_msg
            
        return message

    def _format_search_response(self, keyword: str, matches: list) -> str:
        """Structured, clear answer format."""
        symbol = self._get_active_currency()
        income = sum(t.amount for t in matches if t.type == "credit")
        outflow = sum(t.amount for t in matches if t.type == "debit")
        
        res = f"## 🔍 Result: {keyword}\n\n"
        res += f"| Direction | Total Sum | Count |\n"
        res += f"| :--- | :--- | :--- |\n"
        res += f"| **Sent** | -{symbol}{outflow:,.2f} | {len([t for t in matches if t.type == 'debit'])} |\n"
        res += f"| **Received** | +{symbol}{income:,.2f} | {len([t for t in matches if t.type == 'credit'])} |\n\n"
        
        res += "### 📝 Details\n"
        res += "| Date | Amount | Description |\n| :--- | :--- | :--- |\n"
        for t in matches[:10]:
            sign = "+" if t.type == "credit" else "-"
            res += f"| {t.date.strftime('%d %b')} | **{sign}{symbol}{t.amount:,.0f}** | {t.description[:25]} |\n"
        return res

    # ==========================================
    # CONTEXT 3: FINANCIAL_AI_PAGE - Chat (LLM ENHANCED)
    # ==========================================
    
    async def chat(self, message: str, chat_history: List = [], context: str = "FINANCIAL_AI_PAGE") -> str:
        """Process user message using LLM for intent understanding."""
        from app.services.llm_service import llm_service
        
        # Handle non-chat contexts directly
        if context == "HOME_PAGE":
            return json.dumps(self.get_home_kpis())
        if context == "TRANSACTIONS_PAGE":
            return self.get_transactions_snapshot()
        
        # FINANCIAL_AI_PAGE - Interactive chat
        txs = storage.get_all_transactions()
        if not txs:
            return "📊 **No transaction data found.**\n\nPlease upload a bank statement to begin analysis."

        try:
            # 1. Classify Intent
            classification = llm_service.classify_intent(message, chat_history)
            intent = classification.get("intent", "CHAT")
            params = classification.get("parameters", {})
            
            print(f"[RagAgent] Intent: {intent}, Params: {params}") # Debug log

            # 2. Route based on Intent
            if intent == "SEARCH":
                return self._handle_llm_search(params, txs)
            
            elif intent == "SUMMARY":
                return await self._handle_llm_summary(message, params, txs)
            
            elif intent == "INSIGHTS":
                return await self._handle_llm_insights(message, params, txs)
            
            else: # CHAT or fallback
                return await self._handle_general_chat(message, txs)

        except Exception as e:
            print(f"[RagAgent] Error in chat loop: {e}")
            import traceback
            traceback.print_exc()
            return "I encountered an error processing your request. Please try again."

    # --- Handlers ---

    def _handle_llm_search(self, params: dict, txs: list) -> str:
        keywords = params.get("keywords", [])
        if not keywords:
            # Fallback if no specific keywords extracted
            return "Could you specify what transaction you are looking for?"
            
        # Combine keywords for a broad search first
        query = " ".join(keywords).lower()
        
        # Smart Search Strategy
        matches = []
        # 1. Exact amount match (if any keyword is a number)
        for k in keywords:
            if str(k).replace('.','',1).isdigit():
                amount = float(k)
                matches.extend([t for t in txs if abs(t.amount - amount) < 0.1])
        
        # 2. Description match
        if not matches:
             matches = [t for t in txs if query in t.description.lower()]
        
        # 3. Individual keyword match (broad)
        if not matches:
            for k in keywords:
                matches.extend([t for t in txs if str(k).lower() in t.description.lower()])
        
        # Deduplicate
        unique_matches = {t.date.isoformat()+t.description: t for t in matches}.values()
        matches = list(unique_matches)

        if not matches:
            return f"## 🔍 No Results Found\n\nI couldn't find any transactions matching **'{query}'**."

        return self._format_search_response(query, matches)

    async def _handle_llm_summary(self, user_query: str, params: dict, txs: list) -> str:
        from app.services.llm_service import llm_service
        
        # Prepare Data Context for LLM
        summ = Analytics.calculate_summary(txs)
        cats = Analytics.calculate_category_breakdown(txs)
        top_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
        
        data_context = f"""
        Total Income: {summ['total_income']}
        Total Expense: {summ['total_expense']}
        Net Balance: {summ['net_balance']}
        
        Top Spending Categories:
        {json.dumps(dict(top_cats), indent=2)}
        """
        
        category_filter = params.get("category")
        if category_filter:
            # Refine context if user asked for specific category
            cat_total = cats.get(category_filter, 0)
            data_context += f"\nSpecific Category '{category_filter}': {cat_total}"

        system_prompt = """You are a financial analyst.
        Generate a concise, markdown-formatted summary based on the provided data.
        Use emojis. Use tables for metrics.
        The user asked for: "{user_query}"
        """
        
        return llm_service.generate_response(system_prompt, user_query, data_context)

    async def _handle_llm_insights(self, user_query: str, params: dict, txs: list) -> str:
        from app.services.llm_service import llm_service
        
        # Basic analytics
        trends = Analytics.calculate_monthly_trends(txs)
        highest_debit = max([t for t in txs if t.type == "debit"], key=lambda x: x.amount, default=None)
        
        data_context = f"""
        Monthly Trends: {json.dumps(trends, indent=2)}
        Highest Single Expense: {highest_debit.amount if highest_debit else 0} ({highest_debit.description if highest_debit else 'N/A'})
        """
        
        system_prompt = "You provide financial insights. Be brief and data-driven."
        return llm_service.generate_response(system_prompt, user_query, data_context)
        
    async def _handle_general_chat(self, user_query: str, txs: list) -> str:
        from app.services.llm_service import llm_service
        
        # Just give basic context
        summ = Analytics.calculate_summary(txs)
        data_context = f"User Balance: {summ['net_balance']}"
        
        system_prompt = "You are a helpful assistant for a financial dashboard. Answer generally. Do not make up transaction data."
        return llm_service.generate_response(system_prompt, user_query, data_context)


# Singleton instance
rag_agent = RagAgent()
