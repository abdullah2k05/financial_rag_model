from app.services.storage import storage
from app.services.analytics import Analytics
import json

txns = storage.get_all_transactions()
print("TRANSACTION_COUNT:", len(txns))

summary = Analytics.calculate_summary(txns)
print("TOTAL_INCOME:", summary["total_income"])
print("TOTAL_EXPENSE:", summary["total_expense"])
print("NET_BALANCE:", summary["net_balance"])
print("COUNT:", summary["transaction_count"])

categories = Analytics.calculate_category_breakdown(txns)
for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    print(f"CAT|{cat}|{amt}")

trends = Analytics.calculate_monthly_trends(txns)
for month, data in sorted(trends.items()):
    print(f"TREND|{month}|{data['income']}|{data['expense']}")

top = Analytics.calculate_top_merchants(txns, limit=10)
for m in top:
    print(f"MERCHANT|{m['name']}|{m['value']}")

if txns:
    print("CURRENCY:", txns[0].currency)
    dates = sorted([t.date for t in txns])
    print("DATE_FROM:", dates[0].strftime("%Y-%m-%d"))
    print("DATE_TO:", dates[-1].strftime("%Y-%m-%d"))
