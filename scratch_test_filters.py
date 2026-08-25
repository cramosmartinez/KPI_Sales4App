import urllib.parse
import urllib.request
import json

base_url = "https://kpi-sales4app.onrender.com/api/sales4app/vendedores"
params = {
    "anio": "2025",
    "mes": "1,2",
    "empresa": "FACA,FALE",
    "grupo": "GB,NR"
}
query_str = urllib.parse.urlencode(params)
print("Querying:", query_str)
try:
    with urllib.request.urlopen(f"{base_url}?{query_str}") as response:
        print("Status:", response.status)
        data = json.loads(response.read())
        print("Data items:", len(data))
except Exception as e:
    print("Error:", e)
