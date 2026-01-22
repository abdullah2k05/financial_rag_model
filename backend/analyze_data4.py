from app.services.storage import storage
from app.services.analytics import Analytics
import sys

# Force UTF-8 
sys.stdout.reconfigure(encoding='utf-8')

txns = storage.get_all_transactions()

# Monthly trends
trends = Analytics.calculate_monthly_trends(txns)
print("MONTHLY TRENDS:")
for month, data in sorted(trends.items()):
    net = data['income'] - data['expense']
    print(f"  {month}: +{data['income']:,.0f} / -{data['expense']:,.0f} = {net:,.0f}")

print("")
print("TOP 10 MERCHANTS BY SPENDING:")
top = Analytics.calculate_top_merchants(txns, limit=10)
for i, m in enumerate(top, 1):
    name = m['name'][:35]
    print(f"  {i}. {name}: {m['value']:,.0f}")
