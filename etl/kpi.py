import pandas as pd

def _n(row, col):
    try:
        v = row.get(col)
        if v is None: return None
        f = float(str(v).replace(',','.').replace('$','').replace('%','').strip())
        return None if pd.isna(f) else f
    except:
        return None

def ultimo_mes(df_kpi: pd.DataFrame) -> pd.Timestamp:
    df = df_kpi.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["ventas"] = pd.to_numeric(df["ventas"].astype(str).str.replace(',','.'), errors="coerce")
    df = df.dropna(subset=["ventas","fecha"])
    if df.empty: return None
    return df["fecha"].max()

def kpi_mes(df_kpi: pd.DataFrame, fecha: pd.Timestamp) -> dict:
    df = df_kpi.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    row = df[df["fecha"].dt.to_period("M") == fecha.to_period("M")]
    if row.empty: return {}
    r = row.iloc[0]
    return {k: _n(r, k) for k in [
        "fecha","ventas","inversion_medios","otros_gastos_mkt",
        "presupuesto_total","ratio_presupuesto_ventas",
        "leads_validados","clientes_nuevos"
    ]}

def mes_anterior(df_kpi: pd.DataFrame, fecha: pd.Timestamp) -> dict:
    return kpi_mes(df_kpi, fecha - pd.DateOffset(months=1))

def variacion_pct(actual, anterior):
    try:
        a, b = float(actual), float(anterior)
        return (a - b) / abs(b) if b != 0 else None
    except:
        return None
