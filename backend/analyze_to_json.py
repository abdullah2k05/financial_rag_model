from app.services.storage import storage
from app.services.analytics import Analytics
import json

txns = storage.get_all_transactions()
summary = Analytics.calculate_summary(txns)
categories = Analytics.calculate_category_breakdown(txns)
trends = Analytics.calculate_monthly_trends(txns)
top = Analytics.calculate_top_merchants(txns, limit=10)

result = {
    "transaction_count": len(txns),
    "currency": txns[0].currency if txns else "N/A",
    "date_from": min(t.date for t in txns).strftime("%Y-%m-%d") if txns else "N/A",
    "date_to": max(t.date for t in txns).strftime("%Y-%m-%d") if txns else "N/A",
    "summary": summary,
    "categories": categories,
    "monthly_trends": trends,
    "top_merchants": top
}

with open("analysis_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("Done")
