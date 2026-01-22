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
        """Process user message using Grounded RAG (Deterministic Analytics + Vector Retrieval)."""

        from app.services.llm_service import llm_service
        from app.services.vector_store import vector_store

        # Handle non-chat contexts directly (JSON/Markdown snapshots)
        if context == "HOME_PAGE":
            return json.dumps(self.get_home_kpis())
        if context == "TRANSACTIONS_PAGE":
            return self.get_transactions_snapshot()

        # FINANCIAL_AI_PAGE - Interactive grounded chat
        txs = storage.get_all_transactions()
        if not txs:
            return "📊 **No transaction data found.**\n\nPlease upload a bank statement to begin analysis."

        try:
            # 1. Deterministic Analytics (Authoritative Truth)
            # These values are computed by our python logic, not the LLM.
            summ = Analytics.calculate_summary(txs)
            cats = Analytics.calculate_category_breakdown(txs)
            top_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
            symbol = self._get_active_currency()
            # 2. Vector Retrieval (Granular Transaction Details)
            # First, classify intent to get keywords for better search
            from app.services.llm_service import llm_service
            intent_data = llm_service.classify_intent(message, [])
            intent = intent_data.get("intent", "CHAT")
            keywords = intent_data.get("parameters", {}).get("keywords", [])
            category = intent_data.get("parameters", {}).get("category", "")
            search_query = message
            if keywords:
                search_query = " ".join(keywords)

            # For queries requiring exact sums, compute in Python to avoid LLM errors
            msg_lower = message.lower()
            is_sum_query = any(word in msg_lower for word in ["how much", "total", "sum", "amount", "spent", "received", "sent"])
            if intent == "SUMMARY" and category and category in cats:
                total = cats[category]
                return f"## Spending Analysis: {category.title()}\n\n**Total Amount**: {symbol}{total:,.2f}"
            elif (intent == "SEARCH" and keywords) or is_sum_query:
                # Find transactions matching keywords and compute sums
                matching_txs = []
                for tx in txs:
                    desc_lower = tx.description.lower()
                    if any(kw.lower() in desc_lower for kw in keywords):
                        matching_txs.append(tx)
                if matching_txs:
                    sent = sum(tx.amount for tx in matching_txs if tx.type == "debit")
                    received = sum(tx.amount for tx in matching_txs if tx.type == "credit")
                    count = len(matching_txs)
                    response = f"## Transaction Analysis: {' '.join(keywords).title()}\n\n"
                    response += f"### Financial Summary\n"
                    response += f"| Metric | Amount |\n"
                    response += f"|--------|--------|\n"
                    response += f"| **Total Sent** | {symbol}{sent:,.2f} |\n"
                    response += f"| **Total Received** | {symbol}{received:,.2f} |\n"
                    response += f"| **Net Flow** | {symbol}{received - sent:,.2f} |\n"
                    response += f"| **Transactions** | {count} |\n\n"
                    response += f"### Transaction Details\n"
                    response += f"| Date | Amount | Description |\n"
                    response += f"|------|--------|-------------|\n"
                    for tx in sorted(matching_txs, key=lambda x: x.date, reverse=True)[:20]:  # Show up to 20, sorted by date desc
                        sign = "-" if tx.type == "debit" else "+"
                        direction = "Sent" if tx.type == "debit" else "Received"
                        response += f"| {tx.date.strftime('%b %d, %Y')} | **{direction} {symbol}{tx.amount:,.0f}** | {tx.description[:50]} |\n"
                    return response

            # Include category details if relevant
            cat_details = ""
            if intent == "SUMMARY" or category:
                cat_details = f"- **Category Breakdown**: {', '.join([f'{c}: {symbol}{v:,.2f}' for c, v in top_cats])}"
                if category and category in cats:
                    cat_details += f"\n- **{category} Spending**: {symbol}{cats[category]:,.2f}"

            # If specific category query, compute exact sum from transactions
            specific_sum = None
            if category and category in cats:
                specific_sum = cats[category]
            elif intent == "SEARCH" and keywords:
                # For search queries, sum the amounts from retrieved chunks
                # But chunks are retrieved after, so perhaps sum all matching category or description
                # For now, if category detected, use cats[category]
                pass

            authoritative_context = f"""
### AUTHORITATIVE FINANCIAL SUMMARY (READ-ONLY TRUTH)
- **Total Income**: {symbol}{summ['total_income']:,.2f}
- **Total Spending**: {symbol}{summ['total_expense']:,.2f}
- **Net Balance**: {symbol}{summ['net_balance']:,.2f}
{cat_details}
"""
            # Find the most relevant lines from the CSV
            chunks = vector_store.search(search_query, k=10)
            retrieved_context = "\n".join([f"• {doc.page_content}" for doc in chunks])

            # 3. Construct Grounded System Prompt (Structured & Clear Formatting)
            system_prompt = f"""You are a specialized Financial Data Analyst.
Provide clear, structured answers with proper formatting and currency symbols.

PROFESSIONAL FORMATTING GUIDELINES:
- Structure responses with clear headings and sections
- Use tables for summaries and detailed lists
- Bold only key amounts and totals
- ALWAYS use the currency symbol ({symbol}) for ALL monetary values - never use $ or other symbols
- Present sent/received transactions clearly differentiated
- Show transaction counts and net flows where applicable
- Maintain concise, informative language
- IMPORTANT: Use only the exact figures from AUTHORITATIVE DATA - do not calculate or estimate

### AUTHORITATIVE DATA
{authoritative_context.strip()}

### RETRIEVED TRANSACTIONS
{retrieved_context}
"""

            # 4. Single-Call Generation
            response = llm_service.generate_response(system_prompt, message, "Grounding Context Provided in System Prompt")
            return response

        except Exception as e:
            print(f"[RagAgent] Error in RAG loop: {e}")
            import traceback
            traceback.print_exc()
            return "I encountered an error processing your financial query. Please try again."



# Singleton instance
rag_agent = RagAgent()
