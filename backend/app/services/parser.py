import io
from typing import List, Tuple, Optional

import pandas as pd
import dateparser

from app.models.transaction import Transaction, StatementMetadata


class UniversalCSVParser:
    """Pandas-based CSV parser for bank statements.

    Designed to work with files like:

        00300109448879,
        Opening Balance,PKR      174157.29
        Closing Balance,PKR      48336.29
        Currency,Pakistan Rupee(PKR)
        Booking Date,Value Date,Doc No,Description,Debit,Credit,Available Balance
        01 Dec 2025,01 Dec 2025,,...,1100.00,,373057.29

    We:
      - Detect and skip metadata lines above the real header
      - Use pandas.read_csv with engine="python" so we do NOT get C-engine
        tokenizing errors like "Expected 2 fields in line 5, saw 7".
    """

    async def parse(self, file_content: bytes, filename: str) -> Tuple[List[Transaction], StatementMetadata]:
        # 1) Decode bytes to text
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1", errors="ignore")

        # 2) Split into non-empty lines
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Empty file")

        # 3) Detect header index: prefer line containing 'booking date'
        header_idx = self._find_header_index(lines)
        if header_idx is None:
            raise ValueError("Could not find CSV header line (expected a line with 'Booking Date,...')")

        # 4) Detect delimiter using the header line
        header_line = lines[header_idx]
        delimiter = self._detect_delimiter(header_line)

        # 5) Build a new text starting from the header line so pandas never sees
        #    the short metadata lines above it (the original source of the
        #    'Expected 2 fields in line 5, saw 7' error).
        data_str = "\n".join(lines[header_idx:])

        try:
            df = pd.read_csv(
                io.StringIO(data_str),
                sep=delimiter,
                header=0,            # first line of data_str is the header
                engine="python",    # avoid C-engine tokenizing errors
                on_bad_lines="skip", # skip malformed rows instead of raising
                skipinitialspace=True,
            )
        except Exception as e:
            # Surface a clear pandas parsing error up to the API layer
            raise ValueError(f"Pandas failed to read CSV: {str(e)}")

        if df.empty:
            raise ValueError("CSV contains no data rows after header")

        # 6) Detect Currency from metadata lines (lines before header_idx)
        detected_currency = self._detect_currency(lines[:header_idx]) or "USD"

        # 6) Normalize column names and find relevant columns
        df.columns = df.columns.astype(str).str.strip().str.lower()

        def find_col(candidates: List[str]) -> Optional[str]:
            for cand in candidates:
                for col in df.columns:
                    if col == cand:
                        return col
            # fuzzy contains match
            for cand in candidates:
                for col in df.columns:
                    if cand in col:
                        return col
            return None

        date_col = find_col(["booking date", "transaction date", "date"])
        desc_col = find_col(["description", "details", "narrative"])
        debit_col = find_col(["debit"])
        credit_col = find_col(["credit"])
        balance_col = find_col(["available balance", "balance"])

        if date_col is None:
            raise ValueError(f"Could not identify a date column in headers: {list(df.columns)}")

        transactions: List[Transaction] = []

        # 7) Iterate rows and build Transaction objects
        for _, row in df.iterrows():
            try:
                date_val = row[date_col]
                if pd.isna(date_val):
                    continue

                parsed_date = dateparser.parse(str(date_val))
                if not parsed_date:
                    continue

                # Description
                desc = "No Description"
                if desc_col is not None:
                    val = row[desc_col]
                    if not pd.isna(val):
                        desc = str(val)

                # Amount logic: debit/credit columns preferred
                def parse_amt(v) -> float:
                    if pd.isna(v):
                        return 0.0
                    s = str(v)
                    # remove currency symbols and spaces
                    for ch in ["$", "€", "£", "PKR", "pkr"]:
                        s = s.replace(ch, "")
                    s = s.replace(" ", "")
                    # normalize thousands/decimal separators
                    if "," in s and "." in s:
                        if s.rfind(",") > s.rfind("."):
                            s = s.replace(".", "").replace(",", ".")
                        else:
                            s = s.replace(",", "")
                    elif "," in s:
                        parts = s.split(",")
                        if len(parts[-1]) == 2:
                            s = s.replace(",", ".")
                        else:
                            s = s.replace(",", "")
                    try:
                        return float(s)
                    except Exception:
                        return 0.0

                amount = 0.0
                txn_type = "unknown"

                credit_val = parse_amt(row[credit_col]) if credit_col is not None else 0.0
                debit_val = parse_amt(row[debit_col]) if debit_col is not None else 0.0

                if credit_val > 0 and debit_val <= 0:
                    amount = credit_val
                    txn_type = "credit"
                elif debit_val > 0 and credit_val <= 0:
                    amount = debit_val
                    txn_type = "debit"
                else:
                    # If both zero or both positive, skip ambiguous row
                    continue

                # Balance
                balance: Optional[float] = None
                if balance_col is not None:
                    balance = parse_amt(row[balance_col])

                t = Transaction(
                    date=parsed_date,
                    description=desc,
                    amount=amount,
                    currency=detected_currency,
                    type=txn_type,
                    balance=balance,
                    raw_data={},
                )
                transactions.append(t)
            except Exception:
                # Skip any row that still fails
                continue

        if not transactions:
            raise ValueError("No valid transactions found in CSV after parsing")

        metadata = StatementMetadata(
            currency=detected_currency,
            date_range_start=min(t.date for t in transactions),
            date_range_end=max(t.date for t in transactions),
        )

        return transactions, metadata

    def _find_header_index(self, lines: List[str]) -> Optional[int]:
        # Prefer a line that explicitly mentions 'booking date'
        for i, line in enumerate(lines):
            if "booking date" in line.lower():
                return i
        # Fallback: first line that has at least 3 delimiters (4 columns)
        for i, line in enumerate(lines):
            if line.count(",") >= 3 or line.count(";") >= 3:
                return i
        return None

    def _detect_delimiter(self, header_line: str) -> str:
        candidates = [",", ";", "\t", "|"]
        best = ","
        best_count = -1
        for cand in candidates:
            c = header_line.count(cand)
            if c > best_count:
                best_count = c
                best = cand
        return best

    def _detect_currency(self, metadata_lines: List[str]) -> Optional[str]:
        """Scans metadata/heading lines for currency information.

        Handles patterns like:
          - "Currency,Pakistan Rupee(PKR)"
          - "CURRENCY PKR PAKISTANI RUPEE"
          - Any line containing common 3-letter currency codes.
        """
        import re

        # First pass: look for explicit "Currency" label
        for line in metadata_lines:
            lower = line.lower()
            upper = line.upper()

            if "currency" in lower:
                # Try to extract code in parentheses e.g. (PKR) or (USD)
                match = re.search(r"\(([A-Z]{3})\)", upper)
                if match:
                    return match.group(1)

                # Try to extract 3-letter code after comma
                parts = line.split(",")
                if len(parts) > 1:
                    potential_code = parts[1].strip().upper()
                    if len(potential_code) >= 3:
                        for code in ["PKR", "USD", "EUR", "GBP", "INR", "AED", "CAD", "AUD"]:
                            if code in potential_code:
                                return code

                # Fallback: search the whole line for known codes
                for code in ["PKR", "USD", "EUR", "GBP", "INR", "AED", "CAD", "AUD"]:
                    if code in upper:
                        return code

        # Second pass: look across all metadata lines combined (even if they don't say "currency")
        all_text = " ".join(metadata_lines).upper()
        for code in ["PKR", "USD", "EUR", "GBP", "INR", "AED", "CAD", "AUD"]:
            if code in all_text:
                return code

        return None
