import pypdf
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
from app.models.transaction import Transaction

class PDFParser:
    """
    Experimental PDF Parser for bank statements.
    Extracts text and attempts to find transaction rows using heuristics.
    """
    
    def __init__(self):
        # Common transaction pattern: Date Description Amount [Balance]
        # Example: 12/01/2023 AMAZON MARKETPLACE -45.00 1200.00
        self.date_pattern = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})')
        self.amount_pattern = re.compile(r'(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')

    def parse(self, file_path: str) -> List[Transaction]:
        transactions = []
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"

                # Detect currency from the full text (look for common codes/symbols)
                detected_currency = self._detect_currency(text) or "USD"
                
                # Simple line-based extraction logic
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    # Look for date at the start
                    date_match = self.date_pattern.search(line)
                    if date_match:
                        date_str = date_match.group(1)
                        # Remove date from line to find description and amount
                        remaining = line.replace(date_str, '').strip()
                        
                        # Find all amounts in the line
                        amounts = self.amount_pattern.findall(remaining)
                        if amounts:
                            # Usually the last or second to last amount is the transaction amount
                            # Balance might come after. We'll pick the first one as a heuristic if only one,
                            # or try to guess.
                            amount_val = float(amounts[0].replace(',', ''))
                            description = remaining.replace(amounts[0], '').strip()
                            
                            # Clean description
                            description = re.sub(r'\s+', ' ', description)
                            
                            transactions.append(Transaction(
                                date=date_str,
                                description=description,
                                amount=abs(amount_val),
                                type='debit' if amount_val < 0 else 'credit',
                                currency=detected_currency,
                                raw_data={"raw_line": line},
                            ))
                            
        except Exception as e:
            print(f"PDF Parsing error: {e}")
            
        return transactions

    def _detect_currency(self, text: str) -> Optional[str]:
        """Best-effort currency detection from PDF text.

        Looks for common 3-letter currency codes or symbols that usually appear
        near amounts or in a "Currency" line.
        """
        upper = text.upper()
        # Prefer explicit 3-letter codes
        for code in ["PKR", "USD", "EUR", "GBP", "INR", "AED", "CAD", "AUD"]:
            if code in upper:
                return code

        # Fall back to symbols if no code was found
        if "$" in text:
            return "USD"
        if "€" in text:
            return "EUR"
        if "£" in text:
            return "GBP"

        return None

# Singleton instance
pdf_parser = PDFParser()
