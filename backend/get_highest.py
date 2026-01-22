from app.services.storage import storage
import json

txns = storage.get_all_transactions()

# Find highest transaction
highest_credit = max([t for t in txns if t.type == "credit"], key=lambda x: x.amount, default=None)
highest_debit = max([t for t in txns if t.type == "debit"], key=lambda x: x.amount, default=None)

result = {
    "highest_credit": {
        "amount": highest_credit.amount if highest_credit else 0,
        "description": highest_credit.description[:60] if highest_credit else "N/A",
        "date": highest_credit.date.strftime("%Y-%m-%d") if highest_credit else "N/A"
    },
    "highest_debit": {
        "amount": highest_debit.amount if highest_debit else 0,
        "description": highest_debit.description[:60] if highest_debit else "N/A",
        "date": highest_debit.date.strftime("%Y-%m-%d") if highest_debit else "N/A"
    }
}

with open("highest_txns.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print("Done")
