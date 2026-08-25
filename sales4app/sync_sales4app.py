import os
import sys
import pandas as pd
import datetime

# Asegurar que el directorio padre esté en el PATH para poder importar dynamics_sql_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamics_sql_client import get_sql

def run_sync():
    print("Iniciando sincronización de datos de Sales4App...")
    
    # Query optimizada para agrupar montos desde SALESLINE y obtener encabezados desde SALESTABLE
    query = """
    SELECT 
        ST.SALESID,
        ST.CUSTACCOUNT,
        ST.SALESGROUP,
        CASE
            WHEN ST.SALESGROUP IS NULL THEN 'SIN GRUPO'
            WHEN ST.SALESGROUP IN ('JDC') THEN 'CAÑA'
            WHEN ST.SALESGROUP IN ('GA-017','GA-003','GA-016','GA-005','GA-004','GA-001','GA-008') THEN 'GB'
            WHEN ST.SALESGROUP IN ('DSLR','ECC','MDCH','GC','FEPP','GJOH','MKT-DG') THEN 'NR'
            WHEN ST.SALESGROUP IN ('MA','SAS','DBM','ECO','IB','HM','PGB','NA','FXGS','DIG-DG') THEN 'CDD'
            WHEN ST.SALESGROUP IN ('BC','GM','JA','JJ','BF','MKT-PR') THEN 'FINCA'
            WHEN ST.SALESGROUP IN ('HJSG','ILMR','JAVO','MAZ','MKT-JC','OL') THEN 'FAPA'
            WHEN ST.SALESGROUP IN ('HI','RB', 'AB', 'AC', 'AJV', 'EDM', 'JDOC', 'MKT-LF', 'OB', 'OESO') THEN 'FAHO'
            WHEN ST.SALESGROUP IN ('AA','CM','ER','GMA', 'HG', 'MTMG', 'JJ', 'BF', 'MKT-PR') THEN 'FANIC'
            WHEN ST.SALESGROUP IN ('BF-005') THEN 'BF01'
            WHEN ST.SALESGROUP IN ('DM','OFICINA') THEN 'OTROS'
            ELSE 'OTRO / SIN CLASIFICAR'
        END AS grupo_comercial,
        ST.SALESSTATUS,
        ST.DOCUMENTSTATUS,
        ST.CURRENCYCODE,
        ST.CREATEDDATETIME,
        ST.DATAAREAID,
        ST.FAIsFromSales4App,
        ISNULL(D1.NAME, 'Sin Asignar / ' + CAST(ST.WORKERSALESRESPONSIBLE AS VARCHAR)) AS WORKERSALESRESPONSIBLE,
        ISNULL(D2.NAME, 'Sin Asignar / ' + CAST(ST.WorkerSalesTaker AS VARCHAR)) AS WorkerSalesTaker,
        ISNULL(SUM(SL.SALESQTY * SL.SALESPRICE), 0) as MontoTotal,
        COUNT(SL.LINENUM) as TotalLineas
    FROM SALESTABLE ST
    LEFT JOIN SALESLINE SL
        ON ST.SALESID = SL.SALESID
        AND ST.DATAAREAID = SL.DATAAREAID
    LEFT JOIN HCMWORKER H1 ON ST.WORKERSALESRESPONSIBLE = H1.RECID
    LEFT JOIN DIRPARTYTABLE D1 ON H1.PERSON = D1.RECID
    LEFT JOIN HCMWORKER H2 ON ST.WorkerSalesTaker = H2.RECID
    LEFT JOIN DIRPARTYTABLE D2 ON H2.PERSON = D2.RECID
    WHERE YEAR(ST.CREATEDDATETIME) >= 2024
    GROUP BY 
        ST.SALESID,
        ST.CUSTACCOUNT,
        ST.SALESGROUP,
        CASE
            WHEN ST.SALESGROUP IS NULL THEN 'SIN GRUPO'
            WHEN ST.SALESGROUP IN ('JDC') THEN 'CAÑA'
            WHEN ST.SALESGROUP IN ('GA-017','GA-003','GA-016','GA-005','GA-004','GA-001','GA-008') THEN 'GB'
            WHEN ST.SALESGROUP IN ('DSLR','ECC','MDCH','GC','FEPP','GJOH','MKT-DG') THEN 'NR'
            WHEN ST.SALESGROUP IN ('MA','SAS','DBM','ECO','IB','HM','PGB','NA','FXGS','DIG-DG') THEN 'CDD'
            WHEN ST.SALESGROUP IN ('BC','GM','JA','JJ','BF','MKT-PR') THEN 'FINCA'
            WHEN ST.SALESGROUP IN ('HJSG','ILMR','JAVO','MAZ','MKT-JC','OL') THEN 'FAPA'
            WHEN ST.SALESGROUP IN ('HI','RB', 'AB', 'AC', 'AJV', 'EDM', 'JDOC', 'MKT-LF', 'OB', 'OESO') THEN 'FAHO'
            WHEN ST.SALESGROUP IN ('AA','CM','ER','GMA', 'HG', 'MTMG', 'JJ', 'BF', 'MKT-PR') THEN 'FANIC'
            WHEN ST.SALESGROUP IN ('BF-005') THEN 'BF01'
            WHEN ST.SALESGROUP IN ('DM','OFICINA') THEN 'OTROS'
            ELSE 'OTRO / SIN CLASIFICAR'
        END,
        ST.SALESSTATUS,
        ST.DOCUMENTSTATUS,
        ST.CURRENCYCODE,
        ST.CREATEDDATETIME,
        ST.DATAAREAID,
        ST.FAIsFromSales4App,
        ISNULL(D1.NAME, 'Sin Asignar / ' + CAST(ST.WORKERSALESRESPONSIBLE AS VARCHAR)),
        ISNULL(D2.NAME, 'Sin Asignar / ' + CAST(ST.WorkerSalesTaker AS VARCHAR))
    """
    
    try:
        print("Ejecutando consulta a Dynamics...")
        data = get_sql(query)
        
        if not data:
            print("Advertencia: No se recibieron datos.")
            return

        print(f"Se obtuvieron {len(data)} registros. Procesando caché...")
        df = pd.DataFrame(data)
        
        # Procesamiento y limpieza de datos básicos
        # Convertir a datetime si es necesario
        df['CREATEDDATETIME'] = pd.to_datetime(df['CREATEDDATETIME'], errors='coerce')
        df['Year'] = df['CREATEDDATETIME'].dt.year
        df['Month'] = df['CREATEDDATETIME'].dt.month
        
        # Asegurar que los montos sean numéricos
        df['MontoTotal'] = pd.to_numeric(df['MontoTotal'], errors='coerce').fillna(0)
        
        # Asegurar que el flag de app sea numérico (1 o 0)
        df['FAIsFromSales4App'] = pd.to_numeric(df['FAIsFromSales4App'], errors='coerce').fillna(0).astype(int)
        
        # Asegurar TotalLineas numérico
        df['TotalLineas'] = pd.to_numeric(df['TotalLineas'], errors='coerce').fillna(0).astype('int32')
        
        # MontoTotal
        df['MontoTotal'] = pd.to_numeric(df['MontoTotal'], errors='coerce').fillna(0).astype('float32')
        
        # Convertir a Categorías para ahorrar RAM
        for col in ['DATAAREAID', 'grupo_comercial', 'WORKERSALESRESPONSIBLE', 'WorkerSalesTaker', 'FAIsFromSales4App']:
            if col in df.columns:
                df[col] = df[col].astype('category')
        
        # Downcast enteros
        df['Year'] = df['Year'].astype('int16')
        df['Month'] = df['Month'].astype('int8')
        
        # Asegurar carpeta data/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        parquet_path = os.path.join(data_dir, 'sales4app_data.parquet')
        
        print(f"Guardando datos en {parquet_path}...")
        df.to_parquet(parquet_path, engine='pyarrow', index=False)
        
        print("Sincronización completada exitosamente!")
        
    except Exception as e:
        print(f"Error durante la sincronización: {e}")

if __name__ == "__main__":
    run_sync()
