from typing import List, Dict
from app.models.transaction import Transaction
from collections import defaultdict
from datetime import datetime

class Analytics:
    @staticmethod
    def calculate_summary(transactions: List[Transaction]) -> Dict:
        """
        Calculates high-level totals: income, expenses, and net balance.
        """
        total_income = sum(t.amount for t in transactions if t.type.lower() == "credit")
        total_expense = sum(t.amount for t in transactions if t.type.lower() == "debit")
        net_balance = total_income - total_expense
        
        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_balance": round(net_balance, 2),
            "transaction_count": len(transactions)
        }

    @staticmethod
    def calculate_category_breakdown(transactions: List[Transaction]) -> Dict[str, float]:
        """
        Calculates spending per category.
        """
        breakdown = defaultdict(float)
        for t in transactions:
            if t.type.lower() == "debit": # Focus on spending
                breakdown[t.category or "Uncategorized"] += t.amount
                
        # Round values
        return {cat: round(amt, 2) for cat, amt in breakdown.items()}

    @staticmethod
    def calculate_monthly_trends(transactions: List[Transaction]) -> Dict[str, Dict[str, float]]:
        """
        Groups transactions by month and calculates income vs expenses.
        """
        trends = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for t in transactions:
            month_key = t.date.strftime("%Y-%m")
            if t.type.lower() == "credit":
                trends[month_key]["income"] += t.amount
            elif t.type.lower() == "debit":
                trends[month_key]["expense"] += t.amount
                
        # Round values
        for month in trends:
            trends[month]["income"] = round(trends[month]["income"], 2)
            trends[month]["expense"] = round(trends[month]["expense"], 2)
            
        return dict(sorted(trends.items()))

    @staticmethod
    def calculate_top_merchants(transactions: List[Transaction], limit: int = 5) -> List[Dict]:
        """
        Identifies the top entities/merchants by total spend.
        """
        merchants = defaultdict(float)
        for t in transactions:
            if t.type.lower() == "debit":
                # Basic cleaning of description to group similar merchants
                # This could be improved with better NLP or regex
                merchant = t.description.split('-')[0].strip()
                merchants[merchant] += t.amount
        
        sorted_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)
        return [{"name": name, "value": round(amt, 2)} for name, amt in sorted_merchants[:limit]]
