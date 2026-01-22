import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from app.models.transaction import Transaction

DB_PATH = "finance.db"

class TransactionStorage:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT,
                amount REAL,
                currency TEXT,
                type TEXT,
                category TEXT,
                balance REAL,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_transactions(self, transactions: List[Transaction]):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        data_to_insert = []
        for t in transactions:
            data_to_insert.append((
                t.date.isoformat(),
                t.description,
                t.amount,
                t.currency,
                t.type,
                t.category,
                t.balance,
                json.dumps(t.raw_data) if t.raw_data else "{}"
            ))
        
        cursor.executemany("""
            INSERT INTO transactions (date, description, amount, currency, type, category, balance, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data_to_insert)
        
        conn.commit()
        conn.close()

    def get_all_transactions(self) -> List[Transaction]:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            t = Transaction(
                date=datetime.fromisoformat(row["date"]),
                description=row["description"],
                amount=row["amount"],
                currency=row["currency"],
                type=row["type"],
                category=row["category"],
                balance=row["balance"],
                raw_data=json.loads(row["raw_data"]) if row["raw_data"] else {}
            )
            # t.id = row["id"] # If we added ID to the model
            results.append(t)
            
        conn.close()
        return results

    def clear_all(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        conn.commit()
        conn.close()

# Singleton instance
storage = TransactionStorage()

