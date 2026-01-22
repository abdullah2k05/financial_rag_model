from app.services.storage import storage
from app.services.analytics import Analytics
import json

txns = storage.get_all_transactions()
print("=== TRANSACTION COUNT ===")
print(len(txns))

print("\n=== SUMMARY ===")
summary = Analytics.calculate_summary(txns)
print(json.dumps(summary, indent=2))

print("\n=== CATEGORY BREAKDOWN ===")
categories = Analytics.calculate_category_breakdown(txns)
print(json.dumps(categories, indent=2))

print("\n=== MONTHLY TRENDS ===")
trends = Analytics.calculate_monthly_trends(txns)
print(json.dumps(trends, indent=2))

print("\n=== TOP MERCHANTS ===")
top = Analytics.calculate_top_merchants(txns, limit=10)
print(json.dumps(top, indent=2))

print("\n=== CURRENCY ===")
if txns:
    print(txns[0].currency)

print("\n=== DATE RANGE ===")
if txns:
    dates = sorted([t.date for t in txns])
    print("From:", dates[0].strftime("%Y-%m-%d"))
    print("To:", dates[-1].strftime("%Y-%m-%d"))
