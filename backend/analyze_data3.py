from app.services.storage import storage
from app.services.analytics import Analytics

txns = storage.get_all_transactions()

# Monthly trends
trends = Analytics.calculate_monthly_trends(txns)
print("=== MONTHLY TRENDS ===")
for month, data in sorted(trends.items()):
    print(f"{month}: Income={data['income']}, Expense={data['expense']}")

print("\n=== TOP MERCHANTS ===")
top = Analytics.calculate_top_merchants(txns, limit=10)
for i, m in enumerate(top, 1):
    print(f"{i}. {m['name'][:40]}: {m['value']}")
