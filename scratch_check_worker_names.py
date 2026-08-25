import os
import sys

# Ensure KPI_Sales4App is in path
sys.path.append(r"c:\Users\cramos\Documents\KPI_Sales4App")

from dynamics_sql_client import get_sql

query = """
SELECT TOP 5 WORKERSALESRESPONSIBLE, WorkerSalesTaker
FROM SALESTABLE
WHERE WORKERSALESRESPONSIBLE IS NOT NULL AND WORKERSALESRESPONSIBLE != 0
"""
res = get_sql(query)
print("Samples from SALESTABLE:", res)

# Try joining HCMWORKER
query2 = """
SELECT TOP 5 
    ST.WORKERSALESRESPONSIBLE, 
    HW.PERSONNELNUMBER,
    DP.NAME
FROM SALESTABLE ST
LEFT JOIN HCMWORKER HW ON ST.WORKERSALESRESPONSIBLE = HW.RECID
LEFT JOIN DIRPARTYTABLE DP ON HW.PERSON = DP.RECID
WHERE ST.WORKERSALESRESPONSIBLE IS NOT NULL AND ST.WORKERSALESRESPONSIBLE != 0
"""
try:
    res2 = get_sql(query2)
    print("Join with HCMWORKER:", res2)
except Exception as e:
    print("Error joining HCMWORKER:", e)
