import csv
import io
from typing import List, Tuple, Optional

import dateparser

from app.models.transaction import Transaction, StatementMetadata


class UniversalCSVParser:
    """A simple, pandas-free CSV parser tailored for bank statements.

    It is designed to handle files like:

        00300109448879,
        Opening Balance,PKR      174157.29
        Closing Balance,PKR      48336.29
        Currency,Pakistan Rupee(PKR)
        Booking Date,Value Date,Doc No,Description,Debit,Credit,Available Balance
        01 Dec 2025,01 Dec 2025,,...,1100.00,,373057.29

    We:
      - Decode bytes safely
      - Skip metadata lines before the real header
      - Use Python's csv.reader so there is no pandas tokenizing error
    """

    def __init__(self) -> None:
        pass

    async def parse(self, file_content: bytes, filename: str) -> Tuple[List[Transaction], StatementMetadata]:
        # 1) Decode
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1", errors="ignore")

        # 2) Split into non-empty logical lines
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Empty file")

        # 3) Detect delimiter (comma vs semicolon vs tab)
        delimiter = self._detect_delimiter(lines)

        # 4) Find header row: look for a line containing 'booking date' (case-insensitive).
        header_index = self._find_header_index(lines, delimiter)
        if header_index is None:
            raise ValueError("Could not find header line (expected something like 'Booking Date,...')")

        header_line = lines[header_index]
        header_reader = csv.reader([header_line], delimiter=delimiter)
        headers = next(header_reader)
        norm_headers = [h.strip().lower() for h in headers]

        # Map expected column names to indices
        idx_booking_date = self._find_column(norm_headers, ["booking date", "date"])
        idx_value_date = self._find_column(norm_headers, ["value date"])
        idx_doc_no = self._find_column(norm_headers, ["doc no", "doc #", "document no"])
        idx_desc = self._find_column(norm_headers, ["description", "details", "narrative"])
        idx_debit = self._find_column(norm_headers, ["debit"])
        idx_credit = self._find_column(norm_headers, ["credit"])
        idx_balance = self._find_column(norm_headers, ["available balance", "balance"])

        if idx_booking_date is None and idx_value_date is None:
            raise ValueError(f"Could not locate a date column in header: {headers}")

        transactions: List[Transaction] = []

        # 5) Parse all data rows after the header
        data_lines = lines[header_index + 1 :]
        reader = csv.reader(data_lines, delimiter=delimiter)

        for row in reader:
            if not row:
                continue

            # Ensure row has at least as many columns as the header; pad if short
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            elif len(row) > len(headers):
                row = row[: len(headers)]

            # Date
            date_str = ""
            if idx_booking_date is not None:
                date_str = row[idx_booking_date]
            elif idx_value_date is not None:
                date_str = row[idx_value_date]

            parsed_date = self._parse_date(date_str)
            if parsed_date is None:
                continue

            # Description
            desc = "No Description"
            if idx_desc is not None:
                desc_val = row[idx_desc].strip()
                if desc_val:
                    desc = desc_val

            # Amount & type
            debit_val = self._parse_amount(row[idx_debit]) if idx_debit is not None else 0.0
            credit_val = self._parse_amount(row[idx_credit]) if idx_credit is not None else 0.0

            if debit_val == 0 and credit_val == 0:
                # informational / non-monetary row; skip for now
                continue

            if credit_val > 0 and debit_val <= 0:
                amount = credit_val
                txn_type = "credit"
            elif debit_val > 0 and credit_val <= 0:
                amount = debit_val
                txn_type = "debit"
            else:
                # Ambiguous; skip
                continue

            # Balance
            balance: Optional[float] = None
            if idx_balance is not None:
                balance = self._parse_amount(row[idx_balance])

            txn = Transaction(
                date=parsed_date,
                description=desc,
                amount=amount,
                currency="PKR",  # this statement appears to be PKR
                type=txn_type,
                balance=balance,
                raw_data={},
            )
            transactions.append(txn)

        if not transactions:
            raise ValueError("No valid transactions found in CSV")

        # Basic metadata; we keep it simple
        metadata = StatementMetadata(
            currency="PKR",
            date_range_start=min(t.date for t in transactions),
            date_range_end=max(t.date for t in transactions),
        )

        return transactions, metadata

    def _detect_delimiter(self, lines: List[str]) -> str:
        """Pick the delimiter that appears most often in the first few lines."""
        candidates = [",", ";", "\t", "|"]
        best = ","
        best_count = -1
        for line in lines[:20]:
            for cand in candidates:
                c = line.count(cand)
                if c > best_count:
                    best_count = c
                    best = cand
        return best

    def _find_header_index(self, lines: List[str], delimiter: str) -> Optional[int]:
        # Prefer a line that explicitly mentions 'booking date'
        for i, line in enumerate(lines):
            if "booking date" in line.lower():
                return i

        # Fallback: first line that looks like it has 4+ columns
        for i, line in enumerate(lines):
            if line.count(delimiter) >= 3:
                return i
        return None

    def _find_column(self, norm_headers: List[str], candidates: List[str]) -> Optional[int]:
        for cand in candidates:
            for i, h in enumerate(norm_headers):
                if cand == h:
                    return i
        # Try fuzzy contains match
        for cand in candidates:
            for i, h in enumerate(norm_headers):
                if cand in h:
                    return i
        return None

    def _parse_date(self, value: str):
        value = (value or "").strip()
        if not value:
            return None
        try:
            dt = dateparser.parse(value)
        except Exception:
            return None
        return dt

    def _parse_amount(self, value: str) -> float:
        if value is None:
            return 0.0
        s = str(value).strip()
        if not s:
            return 0.0
        # Remove common currency symbols and spaces
        for ch in ["$", "€", "£", "PKR", "pkr"]:
            s = s.replace(ch, "")
        s = s.replace(" ", "")

        # Normalize thousands/decimal separators: handle cases like 1,234.56 or 1.234,56
        if "," in s and "." in s:
            # Decide by last separator position
            if s.rfind(",") > s.rfind("."):
                # comma as decimal
                s = s.replace(".", "").replace(",", ".")
            else:
                # dot as decimal, commas as thousands
                s = s.replace(",", "")
        elif "," in s:
            parts = s.split(",")
            if len(parts[-1]) == 2:
                # treat comma as decimal
                s = s.replace(",", ".")
            else:
                # thousands separator
                s = s.replace(",", "")

        try:
            return float(s)
        except Exception:
            return 0.0
