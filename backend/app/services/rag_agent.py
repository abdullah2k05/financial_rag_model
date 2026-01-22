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
        debits = [t for t in txs if t.type.lower() == "debit"]
        credits = [t for t in txs if t.type.lower() == "credit"]
        
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
        income = sum(t.amount for t in matches if t.type.lower() == "credit")
        outflow = sum(t.amount for t in matches if t.type.lower() == "debit")
        
        res = f"## 🔍 Result: {keyword}\n\n"
        res += f"| Direction | Total Sum | Count |\n"
        res += f"| :--- | :--- | :--- |\n"
        res += f"| **Sent** | -{symbol}{outflow:,.2f} | {len([t for t in matches if t.type.lower() == 'debit'])} |\n"
        res += f"| **Received** | +{symbol}{income:,.2f} | {len([t for t in matches if t.type.lower() == 'credit'])} |\n\n"
        
        res += "### 📝 Details\n"
        res += "| Date | Amount | Description |\n| :--- | :--- | :--- |\n"
        for t in matches[:10]:
            sign = "+" if t.type.lower() == "credit" else "-"
            res += f"| {t.date.strftime('%d %b')} | **{sign}{symbol}{t.amount:,.0f}** | {t.description[:25]} |\n"
        return res

    # ==========================================
    # CONTEXT 3: FINANCIAL_AI_PAGE - Chat (LLM ENHANCED)
    # ==========================================
    
    async def chat(self, message: str, chat_history: Optional[List] = None, context: str = "FINANCIAL_AI_PAGE") -> str:
        """Process user message using Grounded RAG (Deterministic Analytics + Vector Retrieval)."""
        if chat_history is None:
            chat_history = []
            
        from app.services.llm_service import llm_service
        from app.services.vector_store import vector_store

        # Handle non-chat contexts directly (JSON/Markdown snapshots)
        if context == "HOME_PAGE":
            return json.dumps(self.get_home_kpis())
        if context == "TRANSACTIONS_PAGE":
            return self.get_transactions_snapshot()

        # FINANCIAL_AI_PAGE - Interactive grounded chat
        try:
            print(f"[RagAgent] Chat session started. Context: {context}")
            # 1. Deterministic Analytics
            print("[RagAgent] Computing analytics...")
            txs = storage.get_all_transactions()
            if not txs:
                return "📊 **No transaction data found.**\nPlease upload a bank statement to begin analysis."
                
            summ = Analytics.calculate_summary(txs)
            cats = Analytics.calculate_category_breakdown(txs)
            top_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
            symbol = self._get_active_currency()

            # Additional facts for authoritative data
            debits = [t for t in txs if t.type.lower() == "debit"]
            credits = [t for t in txs if t.type.lower() == "credit"]
            highest_debit = max(debits, key=lambda x: x.amount, default=None)
            highest_credit = max(credits, key=lambda x: x.amount, default=None)

            # Most frequent merchant (by transaction count)
            merch_freq = {}
            for d in debits:
                merch_freq[d.description] = merch_freq.get(d.description, 0) + 1
            most_freq_merch = max(merch_freq.items(), key=lambda x: x[1], default=(None, 0))

            # Top income source (by amount)
            sender_amount = {}
            for c in credits:
                sender_amount[c.description] = sender_amount.get(c.description, 0) + c.amount
            top_sender = max(sender_amount.items(), key=lambda x: x[1], default=(None, 0))
            
            # 2. Vector Retrieval
            print(f"[RagAgent] Classifying intent (History: {len(chat_history)} turns)...")
            try:
                intent_data = llm_service.classify_intent(message, chat_history)
                if not isinstance(intent_data, dict):
                    print(f"[RagAgent] Warning: classify_intent returned non-dict: {type(intent_data)}")
                    intent_data = {"intent": "CHAT", "parameters": {}}
            except Exception as ie:
                print(f"[RagAgent] Intent classification crashed: {ie}")
                intent_data = {"intent": "CHAT", "parameters": {}}
                
            intent = intent_data.get("intent", "CHAT")
            params = intent_data.get("parameters", {})
            keywords = params.get("keywords", [])
            category = params.get("category", "")
            
            print(f"[RagAgent] Intent: {intent}, Keywords: {keywords}, Category: {category}")
            
            search_query = message

            msg_lower = message.lower()
            is_sum_query = any(word in msg_lower for word in ["how much", "total", "sum", "amount", "spent", "received", "sent", "paid"])
            
            if intent == "SUMMARY":
                if category and category in cats:
                    print(f"[RagAgent] Short-circuit: Summary for {category}")
                    total = cats[category]
                    return f"## Spending Analysis: {category.title()}\n\n**Total Amount**: {symbol}{total:,.2f}"
                elif not category and any(word in msg_lower for word in ["total", "summary", "spending", "income", "balance"]):
                    print(f"[RagAgent] Short-circuit: Global Summary")
                    if "income" in msg_lower or "received" in msg_lower:
                         return f"## Financial Summary: Total Income\n\n**Total Received**: {symbol}{summ['total_income']:,.2f}\n**Transactions**: {len([t for t in txs if t.type.lower() == 'credit'])}"
                    elif "balance" in msg_lower or "net" in msg_lower:
                         return f"## Financial Summary: Net Position\n\n**Income**: {symbol}{summ['total_income']:,.2f}\n**Spending**: {symbol}{summ['total_expense']:,.2f}\n**Net Balance**: {symbol}{summ['net_balance']:,.2f}"
                    else:
                         return f"## Financial Summary: Total Spending\n\n**Total Spent**: {symbol}{summ['total_expense']:,.2f}\n**Transactions**: {len([t for t in txs if t.type.lower() == 'debit'])}"
            
            elif (intent == "SEARCH" and keywords) or (is_sum_query and keywords):
                print(f"[RagAgent] Running Python-based transaction match...")
                filler_words = {"account", "named", "the", "to", "for", "named", "transaction", "payment", "sent", "received", "all", "show", "of", "me", "with", "spend", "spending", "cost", "amount", "total", "sum", "how", "much", "did", "i", "pay"}
                refined_keywords = [kw for kw in keywords if kw.lower() not in filler_words and len(kw) > 1]
                active_keywords = refined_keywords if refined_keywords else keywords
                
                import re
                def tx_matches(tx_desc, kws, strict=False):
                    if strict:
                        return all(re.search(rf'\b{re.escape(kw)}\b', tx_desc, re.IGNORECASE) for kw in kws)
                    return any(re.search(rf'\b{re.escape(kw)}\b', tx_desc, re.IGNORECASE) for kw in kws)

                strict_matches = [tx for tx in txs if tx_matches(tx.description, active_keywords, strict=True)]
                matching_txs = strict_matches if strict_matches else [tx for tx in txs if tx_matches(tx.description, active_keywords, strict=False)]
                
                if matching_txs:
                    print(f"[RagAgent] Found {len(matching_txs)} matching transactions")
                    sent = sum(tx.amount for tx in matching_txs if tx.type.lower() == "debit")
                    received = sum(tx.amount for tx in matching_txs if tx.type.lower() == "credit")
                    count = len(matching_txs)
                    response = f"## Transaction Analysis: {' '.join(active_keywords).title()}\n\n"
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
                    for tx in sorted(matching_txs, key=lambda x: x.date, reverse=True)[:20]:
                        sign = "-" if tx.type.lower() == "debit" else "+"
                        direction = "Sent" if tx.type.lower() == "debit" else "Received"
                        response += f"| {tx.date.strftime('%b %d, %Y')} | **{direction} {symbol}{tx.amount:,.0f}** | {tx.description[:50]} |\n"
                    
                    if count > 20:
                        response += f"\n\n> [!NOTE]\n> Showing the 20 most recent transactions out of {count} total matching records."
                    return response

            # Include category and merchant details if relevant
            merchants = Analytics.calculate_top_merchants(txs, limit=10)
            merch_details = f"- **Top Merchants**: {', '.join([f'{m[0]}: {symbol}{m[1]:,.2f}' for m in [(m['name'], m['value']) for m in merchants]])}"
            
            cat_details = ""
            if intent == "SUMMARY" or category or True: # Always include some breakdown
                cat_details = f"- **Top Categories**: {', '.join([f'{c}: {symbol}{v:,.2f}' for c, v in top_cats])}"
                # Add ALL category breakdowns for comprehensive context
                if cats:
                    all_cats_detail = "\n".join([f"  - {cat}: {symbol}{amt:,.2f}" for cat, amt in sorted(cats.items(), key=lambda x: x[1], reverse=True)])
                    cat_details += f"\n- **Category Breakdown (All)**:\n{all_cats_detail}"
                if category and category in cats:
                    cat_details += f"\n- **{category} Specific Spending**: {symbol}{cats[category]:,.2f}"

            hd_line = f"- **Highest Debit**: {symbol}{highest_debit.amount:,.2f} ({highest_debit.description[:30]}...) on {highest_debit.date.strftime('%b %d')}" if highest_debit else "- **Highest Debit**: N/A"
            hc_line = f"- **Highest Credit**: {symbol}{highest_credit.amount:,.2f} ({highest_credit.description[:30]}...) on {highest_credit.date.strftime('%b %d')}" if highest_credit else "- **Highest Credit**: N/A"
            mf_line = f"- **Most Frequent Merchant**: {most_freq_merch[0][:30]} ({most_freq_merch[1]} transactions)" if most_freq_merch[0] else "- **Most Frequent Merchant**: N/A"
            ts_line = f"- **Top Income Source**: {top_sender[0][:30]} ({symbol}{top_sender[1]:,.2f})" if top_sender[0] else "- **Top Income Source**: N/A"

            authoritative_context = f"""
### AUTHORITATIVE FINANCIAL SUMMARY (COMPLETE DATA)
- **Total Income**: {symbol}{summ['total_income']:,.2f}
- **Total Spending**: {symbol}{summ['total_expense']:,.2f}
- **Net Balance**: {symbol}{summ['net_balance']:,.2f}
{hd_line}
{hc_line}
{mf_line}
{ts_line}
{cat_details}
{merch_details}
"""
            from app.services.vector_store import vector_store
            chunks = vector_store.search(search_query, k=20)  # Increased for better coverage
            print(f"[RagAgent] Retrieved {len(chunks)} context chunks")
            retrieved_context = "\n".join([f"• {doc.page_content}" for doc in chunks])

            system_prompt = f"""You are a specialized Financial Data Analyst with access to comprehensive transaction data.
Your role is to provide accurate, clear answers using the authoritative financial summary provided below.

CORE PRINCIPLES:
- ALWAYS use the exact figures from 'AUTHORITATIVE FINANCIAL DATA' when answering questions about totals, sums, or aggregates
- The authoritative data contains pre-calculated, accurate totals - USE THEM DIRECTLY
- Do NOT attempt to manually sum individual transactions from 'SAMPLE TRANSACTIONS' - those are examples only
- If asked about a specific merchant/entity not in the authoritative data, acknowledge you need to search the detailed transactions
- Provide clear, direct answers with proper currency formatting

RESPONSE FORMATTING:
- Lead with the direct answer (amount or key insight)
- Use tables for summaries and transaction lists
- Bold key amounts and totals  
- ALWAYS include the currency symbol ({symbol}) for monetary values
- Keep responses concise and focused on the user's question

### AUTHORITATIVE FINANCIAL DATA
{authoritative_context.strip()}

### SAMPLE TRANSACTIONS (For context - Do NOT sum these manually)
{retrieved_context}
"""
            print(f"[RagAgent] Calling LLM generate_response...")
            try:
                response = llm_service.generate_response(system_prompt, message, "Financial context provided", history=chat_history)
                return response
            except Exception as ge:
                print(f"[RagAgent] LLM generation crashed: {ge}")
                return "I'm sorry, I'm having trouble connecting to the AI service. The data is safe, but I can't generate a text response right now."

        except Exception as e:
            print(f"[ERROR] RagAgent loop failed: {repr(e)}")
            import traceback
            traceback.print_exc()
            return "I encountered an error processing your financial query. Please try again."



# Singleton instance
rag_agent = RagAgent()
