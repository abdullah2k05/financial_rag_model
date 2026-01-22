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

    # ==========================================
    # CONTEXT 3: FINANCIAL_AI_PAGE - Chat
    # ==========================================
    def _search_transactions(self, keyword: str, strict: bool = True) -> list:
        """Search transactions by keyword. Character-exact per user rules."""
        txs = storage.get_all_transactions()
        k = " ".join(keyword.strip().lower().split())
        
        def normalize(s):
            return " ".join(s.strip().lower().split())

        if strict:
            # Rule 1 & 2: Exact character-exact match constraint
            return [t for t in txs if normalize(t.description) == k]
            
        return [t for t in txs if k in t.description.lower()]

    def _handle_category_query(self, message: str) -> Optional[str]:
        """Handle category-related questions concisely."""
        txs = storage.get_all_transactions()
        if not txs: return None
        symbol = self._get_active_currency()
        cats = Analytics.calculate_category_breakdown(txs)
        
        msg_l = message.lower()
        for cat in cats.keys():
            if cat.lower() in msg_l:
                cat_txs = [t for t in txs if t.category and cat.lower() == t.category.lower()]
                if not cat_txs: cat_txs = [t for t in txs if t.category and cat.lower() in t.category.lower()]
                total = sum(t.amount for t in cat_txs)
                return f"**{cat} Spending:** {symbol}{total:,.2f} ({len(cat_txs)} transactions)."
        
        return None

    def _handle_search_query(self, message: str) -> Optional[str]:
        """Handle exact search for merchants/recipients."""
        txs = storage.get_all_transactions()
        if not txs: return None
        
        # Noise filter: Keep identifiers like 'upi', 'neft' as they are often part of account titles
        noise = {
            'show', 'tell', 'search', 'find', 'what', 'where', 'when', 'how', 'much', 'many', 
            'total', 'spend', 'spending', 'spent', 'transaction', 'transactions', 'payment', 
            'money', 'amount', 'give', 'me', 'the', 'for', 'with', 'from', 'to', 'at', 'is', 
            'are', 'was', 'were', 'credit', 'debit', 'income', 'expense', 'balance', 'highest',
            'largest', 'biggest', 'top', 'bottom', 'details', 'detail', 'list', 'history',
            'summary', 'overview', 'report', 'analysis', 'analyze', 'trend', 'trends',
            'send', 'sent', 'paid', 'pay', 'transfer', 'transferred', 'it', 'me', 'did', 'do',
            'stmt', 'ref', 'payout', 'rs', 'inr', 'rupees', 'rupee', 'and', 'my', 'his', 'her', 
            'in', 'on', 'of', 'i', 'was', 'had', 'were'
        }
        
        # Extract meaningful subject
        words = message.split()
        subjects = [w.strip("?,.!") for w in words if w.strip("?,.!") .lower() not in noise]
        
        if not subjects:
            return None
            
        subject = " ".join(subjects)
        is_strict_hint = any(w.isupper() for w in subjects if len(w) > 2)
        
        # Pass 1: Strict Match (Exact full string)
        matches = self._search_transactions(subject, strict=True)
        
        # Pass 2: Keyword Inclusion Match (Instant)
        if not matches:
             matches = self._search_transactions(subject, strict=False)

        if not matches:
             return f"## 🔍 No Results Found\n\nNo transactions match **'{subject}'**. Try a different name or check your dashboard summary for spelling."

        return self._format_search_response(subject, matches)

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

    async def chat(self, message: str, chat_history: List = [], context: str = "FINANCIAL_AI_PAGE") -> str:
        """Process user message based on context."""
        
        # Handle different contexts
        if context == "HOME_PAGE":
            return json.dumps(self.get_home_kpis())
        
        if context == "TRANSACTIONS_PAGE":
            return self.get_transactions_snapshot()
        
        # FINANCIAL_AI_PAGE - Interactive chat
        message_lower = message.lower()
        txs = storage.get_all_transactions()
        symbol = self._get_active_currency()
        
        if not txs:
            return "📊 **No transaction data found.**\n\nPlease upload a bank statement to begin analysis."
        
        # Rule: Resolve conversational references from memory (Strict Resolution)
        resolved_message = self._resolve_references(message, chat_history)
        
        summ = Analytics.calculate_summary(txs)

        # Search query (Prioritized)
        search_response = self._handle_search_query(resolved_message)
        if search_response:
            return search_response
        
        # Summary requests
        summary_keywords = ["summarize", "overall summary", "full report", "detailed analysis", "snapshot", "how am i doing", "account overview"]
        if any(kw in message_lower for kw in summary_keywords) and len(message.split()) < 5:
            cats = Analytics.calculate_category_breakdown(txs)
            top_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
            cats_text = "\n".join([f"| {c} | {symbol}{a:,.2f} |" for c, a in top_cats])
            
            return f"""## 📊 Financial Summary

### 💰 Key Metrics
| Metric | Amount |
|--------|--------|
| **Net Balance** | **{symbol}{summ['net_balance']:,.2f}** |
| Total Income | +{symbol}{summ['total_income']:,.2f} |
| Total Expenses | -{symbol}{summ['total_expense']:,.2f} |

### 🔍 Top Categories
| Category | Amount |
|----------|--------|
{cats_text}

### 💡 Insight
Your top spending category is **{top_cats[0][0]}**, accounting for significant outflow.
"""
        
        # Income questions
        if "income" in message_lower or "earn" in message_lower or "credit" in message_lower:
            credits = [t for t in txs if t.type == "credit"]
            return f"## 💰 Income Analysis\n\n### 📊 Summary\n**Total Income:** {symbol}{summ['total_income']:,.2f}\n\n### 🔍 Details\n| Metric | Value |\n|--------|-------|\n| **Count** | {len(credits)} |\n| **Average** | {symbol}{summ['total_income']/len(credits):,.2f} |"
        
        # Expense questions
        if "expense" in message_lower or "spend" in message_lower or "spent" in message_lower:
            cats = Analytics.calculate_category_breakdown(txs)
            top_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
            cats_text = "\n".join([f"| {c} | {symbol}{a:,.2f} |" for c, a in top_cats])
            return f"## 💸 Expense Analysis\n\n### 📊 Summary\n**Total Spending:** {symbol}{summ['total_expense']:,.2f}\n\n### 🔍 Details\n| Category | Amount |\n|----------|--------|\n{cats_text}"
        
        # Balance
        if "balance" in message_lower or "net" in message_lower:
            status = "✅ Positive" if summ['net_balance'] >= 0 else "⚠️ Negative"
            return f"## 💵 Net Balance Status\n\n### 📊 Current Position\n# **{symbol}{summ['net_balance']:,.2f}**\n\n### 💡 Insight\nStatus: {status}\nMaintain a positive balance to ensure financial stability."
        
        # Category query
        cat_response = self._handle_category_query(message)
        if cat_response:
            return cat_response
        

        
        # Highest transaction
        if "highest" in message_lower or "largest" in message_lower or "biggest" in message_lower:
            highest_credit = max([t for t in txs if t.type == "credit"], key=lambda x: x.amount, default=None)
            highest_debit = max([t for t in txs if t.type == "debit"], key=lambda x: x.amount, default=None)
            response = "## 🔝 Largest Transactions\n\n### 🔍 Details\n"
            if highest_credit:
                response += f"**Highest Income:** +{symbol}{highest_credit.amount:,.0f}\n> {highest_credit.description[:50]} — *{highest_credit.date.strftime('%b %d, %Y')}*\n\n"
            if highest_debit:
                response += f"**Highest Spending:** -{symbol}{highest_debit.amount:,.0f}\n> {highest_debit.description[:50]} — *{highest_debit.date.strftime('%b %d, %Y')}*"
            return response
        
        # Trends
        if "trend" in message_lower or "month" in message_lower:
            trends = Analytics.calculate_monthly_trends(txs)
            response = "## 📈 Monthly Trends\n\n### 📊 Data Table\n| Month | Income | Expenses | Net |\n|-------|--------|----------|-----|\n"
            for month, data in sorted(trends.items()):
                net = data['income'] - data['expense']
                response += f"| **{month}** | {symbol}{data['income']:,.0f} | {symbol}{data['expense']:,.0f} | **{symbol}{net:,.0f}** |\n"
            
            response += "\n### 💡 Insight\nMonitor these trends to identify seasonal spending or income variances."
            return response
        
        # Default: brief summary
        return f"""## 👋 Hello
        
### 📊 Quick Snapshot
• **Net Balance:** {symbol}{summ['net_balance']:,.2f}
• **Total Transactions:** {len(txs)}

### 💡 Suggestions
Try asking:
• "Summarize my spending"
• "What is my income trends?"
• "Show largest transactions"
"""


# Singleton instance
rag_agent = RagAgent()

