from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import msal
import pandas as pd
import os
import json
from dynamics_sql_client import get_sql

app = Flask(__name__)
CORS(app)

# =====================================
# 🏠 ROOT
# =====================================
@app.route("/", methods=["GET"])
def home():
    return "✅ API FORAGRO funcionando"

# =====================================
# 📦 DATA
# =====================================
@app.route("/empresas")
def empresas():
    query = """
    SELECT DISTINCT DATAAREAID
    FROM SALESTABLE
    ORDER BY DATAAREAID
    """
    return jsonify(get_sql(query))

@app.route("/packingtest", methods=["GET"])
def packingtest():
    query = """
    SELECT TOP 5 *
    FROM CUSTPACKINGSLIPTRANS
    """
    try:
        data = get_sql(query)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/test_salesline_fields", methods=["GET"])
def test_salesline_fields():
    query = """
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'SALESLINE' 
      AND COLUMN_NAME LIKE '%STATUS%'
    ORDER BY COLUMN_NAME
    """
    try:
        data = get_sql(query)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/users", methods=["GET"])
def get_users():
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route("/data", methods=["GET"])
def obtener_data():
    anio = request.args.get("anio")
    mes = request.args.get("mes")
    empresa = request.args.get("empresa")
    cliente = request.args.get("cliente")
    ov = request.args.get("ov")
    limite = request.args.get("limite", 15000)

    filtros = []
    filtros.append("ST.CUSTACCOUNT NOT LIKE 'INT%'")

    if empresa:
        empresas = empresa.split(",")
        lista = ",".join([f"'{e}'" for e in empresas])
        filtros.append(f"ST.DATAAREAID IN ({lista})")

    if anio:
        filtros.append(f"YEAR(ST.CREATEDDATETIME) = {anio}")

    if mes:
        filtros.append(f"MONTH(ST.CREATEDDATETIME) = {mes}")

    if cliente:
        filtros.append(f"ST.CUSTACCOUNT LIKE '%{cliente}%'")

    if ov:
        filtros.append(f"ST.SALESID LIKE '%{ov}%'")

    where = " AND ".join(filtros)
    if where:
        where = "WHERE " + where

    query = f"""
SELECT TOP {limite}
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
    ST.FAIsFromSales4App,  -- 🔥 NUEVO: Campo para identificar OVs de App
    ISNULL(NULLIF(ST.SalesOriginId, ''), 'SIN ORIGEN') AS SalesOriginId,
    
    SL.ITEMID,
    SL.NAME,
    SL.SALESQTY,
    SL.SALESPRICE,
    SL.LINENUM,
    SL.SALESSTATUS AS LINE_STATUS,
    SL.REMAININVENTPHYSICAL,
    SL.INVENTTRANSID,
    SL.DATAAREAID AS LINE_DATAAREAID,
    
    -- 🔥 WMS WORKLINE
    (
        SELECT TOP 1 WL.WORKID 
        FROM WHSWORKLINE WL 
        WHERE WL.INVENTTRANSID = SL.INVENTTRANSID AND WL.DATAAREAID = SL.DATAAREAID
    ) AS WORKID,
    (
        SELECT TOP 1 WL.WORKSTATUS 
        FROM WHSWORKLINE WL 
        WHERE WL.INVENTTRANSID = SL.INVENTTRANSID AND WL.DATAAREAID = SL.DATAAREAID
    ) AS LINE_WORK_STATUS,
    (
        SELECT TOP 1 WT.WORKSTATUS 
        FROM WHSWORKLINE WL
        JOIN WHSWORKTABLE WT ON WL.WORKID = WT.WORKID AND WL.DATAAREAID = WT.DATAAREAID
        WHERE WL.INVENTTRANSID = SL.INVENTTRANSID AND WL.DATAAREAID = WT.DATAAREAID
    ) AS HEADER_WORK_STATUS,
    (
        SELECT TOP 1 WT.WAVEID 
        FROM WHSWORKLINE WL
        JOIN WHSWORKTABLE WT ON WL.WORKID = WT.WORKID AND WL.DATAAREAID = WT.DATAAREAID
        WHERE WL.INVENTTRANSID = SL.INVENTTRANSID AND WL.DATAAREAID = WT.DATAAREAID
    ) AS WAVEID,
    (
        SELECT TOP 1 WT.LOADID 
        FROM WHSWORKLINE WL
        JOIN WHSWORKTABLE WT ON WL.WORKID = WT.WORKID AND WL.DATAAREAID = WT.DATAAREAID
        WHERE WL.INVENTTRANSID = SL.INVENTTRANSID AND WL.DATAAREAID = WT.DATAAREAID
    ) AS LOADID,
    
    -- 🔥 RUTA DE PICKING
    (
        SELECT TOP 1 PR2.PICKINGROUTEID
        FROM WMSPICKINGROUTE PR2
        WHERE PR2.TRANSREFID = ST.SALESID AND PR2.DATAAREAID = ST.DATAAREAID
        ORDER BY PR2.CREATEDDATETIME DESC
    ) AS PICKINGROUTEID,
    
    -- REMISIONES AGRUPADAS
    STUFF((
        SELECT ', ' + CPT2.PACKINGSLIPID
        FROM CUSTPACKINGSLIPTRANS CPT2
        WHERE CPT2.INVENTTRANSID = SL.INVENTTRANSID AND CPT2.DATAAREAID = SL.DATAAREAID
        FOR XML PATH('')
    ), 1, 2, '') AS PACKINGSLIPIDS,
    
    ISNULL((
        SELECT SUM(CPT2.QTY)
        FROM CUSTPACKINGSLIPTRANS CPT2
        WHERE CPT2.INVENTTRANSID = SL.INVENTTRANSID AND CPT2.DATAAREAID = SL.DATAAREAID
    ), 0) AS REMITIDO_TOTAL,
    
    -- ESTADO DE DOCUMENTO POR LÍNEA
    ST.DOCUMENTSTATUS AS LINE_DOCUMENT_STATUS,
    
    -- ESTADO DE ALMACÉN CALCULADO
    CASE 
        WHEN SL.SALESSTATUS IN (2, 3) THEN 'Entregada/Completa'
        WHEN ISNULL(SL.REMAININVENTPHYSICAL, 0) = 0 AND SL.SALESQTY > 0 THEN 'Completa'
        WHEN (SELECT TOP 1 WL.WORKID FROM WHSWORKLINE WL WHERE WL.INVENTTRANSID = SL.INVENTTRANSID AND WL.DATAAREAID = SL.DATAAREAID) IS NOT NULL THEN 'Liberada'
        ELSE 'Pendiente'
    END AS WAREHOUSE_STATUS
    
FROM SALESTABLE ST
INNER JOIN SALESLINE SL
    ON ST.SALESID = SL.SALESID
    AND ST.DATAAREAID = SL.DATAAREAID

{where}

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
    ST.SalesOriginId,
    SL.ITEMID,
    SL.NAME,
    SL.SALESQTY,
    SL.SALESPRICE,
    SL.LINENUM,
    SL.SALESSTATUS,
    SL.REMAININVENTPHYSICAL,
    SL.INVENTTRANSID,
    SL.DATAAREAID

ORDER BY ST.CREATEDDATETIME DESC, SL.LINENUM
"""
    try:
        data = get_sql(query)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================
# 📈 SALES4APP DASHBOARD ENDPOINTS
# =====================================
def get_sales4app_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parquet_path = os.path.join(base_dir, 'data', 'sales4app_data.parquet')
    if not os.path.exists(parquet_path):
        return None
    return pd.read_parquet(parquet_path)

def filter_dataframe(df, request_args):
    if df is None or df.empty:
        return df
    
    anio = request_args.get("anio")
    mes = request_args.get("mes")
    empresa = request_args.get("empresa")
    grupo = request_args.get("grupo")
    
    if anio:
        anios = [int(a.strip()) for a in anio.split(",")]
        df = df[df['Year'].isin(anios)]
    if mes:
        meses = [int(m.strip()) for m in mes.split(",")]
        df = df[df['Month'].isin(meses)]
    if empresa:
        empresas = [e.strip() for e in empresa.split(",")]
        df = df[df['DATAAREAID'].isin(empresas)]
    if grupo:
        grupos = [g.strip() for g in grupo.split(",")]
        df = df[df['grupo_comercial'].isin(grupos)]
        
    return df

@app.route("/api/sales4app/kpis", methods=["GET"])
def sales4app_kpis():
    df = get_sales4app_data()
    if df is None:
        return jsonify({"error": "No hay datos en caché. Ejecute sync_sales4app.py."}), 404
        
    df = filter_dataframe(df, request.args)
    
    total_orders = len(df)
    app_orders = df[df['FAIsFromSales4App'] == 1]
    total_app_orders = len(app_orders)
    
    adoption_rate = (total_app_orders / total_orders * 100) if total_orders > 0 else 0
    total_amount_app = float(app_orders['MontoTotal'].sum())
    
    active_sellers = app_orders['WORKERSALESRESPONSIBLE'].nunique()
    
    return jsonify({
        "total_orders": total_orders,
        "app_orders": total_app_orders,
        "adoption_rate": round(adoption_rate, 2),
        "total_amount_app": total_amount_app,
        "active_sellers": int(active_sellers)
    })

@app.route("/api/sales4app/graficos", methods=["GET"])
def sales4app_graficos():
    df = get_sales4app_data()
    if df is None:
        return jsonify({"error": "No data"}), 404
        
    df = filter_dataframe(df, request.args)
    
    # 1. Tendencia Mensual (Comparativa)
    tendencia = df.groupby(['Year', 'Month', 'FAIsFromSales4App']).size().unstack(fill_value=0).reset_index()
    # Renombrar columnas para facilitar el json
    if 0 not in tendencia.columns: tendencia[0] = 0
    if 1 not in tendencia.columns: tendencia[1] = 0
    tendencia['Mes_Anio'] = tendencia['Month'].astype(str) + '-' + tendencia['Year'].astype(str)
    tendencia_res = {
        "labels": tendencia['Mes_Anio'].tolist(),
        "tradicional": tendencia[0].tolist(),
        "app": tendencia[1].tolist()
    }
    
    # 2. % Adopción por Grupo Comercial
    # Count orders by group and app flag
    group_counts = df.groupby(['grupo_comercial', 'FAIsFromSales4App']).size().unstack(fill_value=0)
    if 0 not in group_counts.columns: group_counts[0] = 0
    if 1 not in group_counts.columns: group_counts[1] = 0
    group_counts['Total'] = group_counts[0] + group_counts[1]
    group_counts['Adopcion'] = (group_counts[1] / group_counts['Total'] * 100).fillna(0).round(2)
    group_counts = group_counts.sort_values(by='Adopcion', ascending=False).reset_index()
    grupos_res = {
        "labels": group_counts['grupo_comercial'].tolist(),
        "adopcion": group_counts['Adopcion'].tolist()
    }
    
    # 3. Distribución por Empresa
    empresa_counts = df[df['FAIsFromSales4App'] == 1].groupby('DATAAREAID').size().reset_index(name='count')
    empresas_res = {
        "labels": empresa_counts['DATAAREAID'].tolist(),
        "data": empresa_counts['count'].tolist()
    }
    
    # 4. Estatus de Órdenes (SalesStatus)
    status_counts = df[df['FAIsFromSales4App'] == 1].groupby('SALESSTATUS').size().reset_index(name='count')
    # SalesStatus en Dynamics enum (ej: 1=Open, 2=Delivered, 3=Invoiced, 4=Canceled) - Mapeo sugerido
    status_map = {1: 'Abierto', 2: 'Entregado', 3: 'Facturado', 4: 'Cancelado'}
    status_counts['status_name'] = status_counts['SALESSTATUS'].map(status_map).fillna(status_counts['SALESSTATUS'].astype(str))
    status_res = {
        "labels": status_counts['status_name'].tolist(),
        "data": status_counts['count'].tolist()
    }
    
    return jsonify({
        "tendencia": tendencia_res,
        "grupos": grupos_res,
        "empresas": empresas_res,
        "estatus": status_res
    })

@app.route("/api/sales4app/vendedores", methods=["GET"])
def sales4app_vendedores():
    df = get_sales4app_data()
    if df is None:
        return jsonify({"error": "No data"}), 404
        
    df = filter_dataframe(df, request.args)
    
    # Agrupar por vendedor responsable y taker
    group = df.groupby(['WORKERSALESRESPONSIBLE', 'WorkerSalesTaker', 'FAIsFromSales4App']).agg(
        OVs=('SALESID', 'count'),
        Monto=('MontoTotal', 'sum'),
        Lineas=('TotalLineas', 'sum')
    ).unstack(fill_value=0).reset_index()
    
    # Aplanar MultiIndex de columnas
    group.columns = ['_'.join(str(c) for c in col).strip('_') for col in group.columns]
    
    # Las columnas generadas serán: OVs_0, OVs_1, Monto_0, Monto_1, Lineas_0, Lineas_1
    for col in ['OVs_0', 'OVs_1', 'Monto_0', 'Monto_1', 'Lineas_0', 'Lineas_1']:
        if col not in group.columns:
            group[col] = 0
            
    group['Total_OVs'] = group['OVs_0'] + group['OVs_1']
    group['Adopcion_Pct'] = (group['OVs_1'] / group['Total_OVs'] * 100).fillna(0).round(2)
    group['Monto_App'] = group['Monto_1'].round(2)
    group['Monto_Trad'] = group['Monto_0'].round(2)
    
    # Nuevas Métricas Comerciales (basadas solo en ventas por App o Totales, elegimos App para Ticket Promedio)
    # Ticket Promedio por App
    group['Ticket_Promedio'] = (group['Monto_1'] / group['OVs_1']).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)
    
    # Promedio de Líneas por OV (App)
    group['Lineas_OV'] = (group['Lineas_1'] / group['OVs_1']).replace([float('inf'), -float('inf')], 0).fillna(0).round(1)
    
    group = group.sort_values(by='Total_OVs', ascending=False)
    
    res = []
    for _, row in group.iterrows():
        res.append({
            "vendedor": row['WORKERSALESRESPONSIBLE'],
            "secretario": row['WorkerSalesTaker'],
            "total_ovs": int(row['Total_OVs']),
            "ovs_app": int(row['OVs_1']),
            "ovs_tradicional": int(row['OVs_0']),
            "adopcion": float(row['Adopcion_Pct']),
            "monto_app": float(row['Monto_App']),
            "monto_tradicional": float(row['Monto_Trad']),
            "ticket_promedio": float(row['Ticket_Promedio']),
            "lineas_promedio": float(row['Lineas_OV'])
        })
        
    return jsonify(res)

@app.route("/api/sales4app/export", methods=["GET"])
def sales4app_export():
    from io import BytesIO
    from flask import send_file
    
    df = get_sales4app_data()
    if df is None:
        return "No data", 404
        
    df = filter_dataframe(df, request.args)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales4App Data')
        
    output.seek(0)
    return send_file(
        output,
        download_name="Sales4App_Report.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =====================================
# 🔄 MANUAL SYNC ENDPOINT (FOR RENDER)
# =====================================
@app.route("/api/sales4app/sync_now", methods=["POST"])
def sales4app_sync_now():
    try:
        from sales4app.sync_sales4app import run_sync
        run_sync()
        return jsonify({"message": "Sincronización completada exitosamente. Caché actualizada."}), 200
    except Exception as e:
        return jsonify({"error": f"Error en sincronización: {str(e)}"}), 500

@app.route("/api/sales4app/empresas", methods=["GET"])
def sales4app_empresas():
    df = get_sales4app_data()
    if df is None:
        return jsonify([])
    empresas = sorted(df['DATAAREAID'].dropna().unique().tolist())
    return jsonify(empresas)

# =====================================
# 🚀 RUN
# =====================================
if __name__ == "__main__":
    print("🚀 API iniciando...")
    app.run(debug=True, port=5000)