import re
from typing import Optional

class Categorizer:
    def __init__(self):
        # Rule-based mapping: keywords to categories
        self.rules = {
            "Housing": ["rent", "mortgage", "housing", "property", "insurance", "hoa"],
            "Utilities": ["electricity", "water", "gas", "internet", "utility", "phone", "mobile", "garbage"],
            "Food & Dining": ["grocery", "supermarket", "restaurant", "cafe", "food", "dining", "uber eats", "doordash", "starbucks", "mcdonalds"],
            "Transportation": ["fuel", "gasoline", "uber", "lyft", "taxi", "train", "bus", "parking", "automotive", "toll"],
            "Entertainment": ["netflix", "spotify", "disney+", "hulu", "cinema", "movie", "game", "hobby", "concert", "theatre"],
            "Shopping": ["amazon", "walmart", "target", "ebay", "clothing", "electronics", "retail", "general"],
            "Healthcare": ["pharmacy", "medical", "doctor", "dentist", "health", "hospital", "clinic", "cvs", "walgreens"],
            "Income": ["salary", "payroll", "dividend", "interest", "tax refund", "venmo", "transfer in"],
            "Financial": ["bank fee", "interest charge", "tax", "investment", "brokerage", "atm"]
        }

    def categorize(self, description: str) -> str:
        desc_lower = description.lower()
        
        # Check rule-based matches
        for category, keywords in self.rules.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', desc_lower):
                    return category
        
        # Fallback for transfers or other patterns
        if "transfer" in desc_lower:
            return "Financial"
            
        return "Uncategorized"

    def apply_categorization(self, transactions):
        """
        Takes a list of Transaction models and updates their category field.
        """
        for t in transactions:
            if not t.category or t.category == "Uncategorized":
                t.category = self.categorize(t.description)
        return transactions

# Singleton instance
categorizer = Categorizer()
