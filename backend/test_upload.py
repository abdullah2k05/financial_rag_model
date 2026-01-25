import requests

url = "https://abdullah2k05-money-lens-backend.hf.space/api/v1/upload"

csv_content = """Date,Description,Amount,Type
2023-10-01,Salary,5000,credit
2023-10-02,Rent,1500,debit
2023-10-05,Groceries,200,debit
"""

files = {'file': ('test.csv', csv_content, 'text/csv')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}") 
except Exception as e:
    print(f"Error: {e}")
