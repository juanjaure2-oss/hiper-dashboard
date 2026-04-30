import pandas as pd

def ultimo_mes(df_kpi: pd.DataFrame) -> pd.Timestamp:
    df = df_kpi.dropna(subset=["ventas"])
    if df.empty:
        return None
    return df["fecha"].max()

def kpi_mes(df_kpi: pd.DataFrame, fecha: pd.Timestamp) -> dict:
    row = df_kpi[df_kpi["fecha"].dt.to_period("M") == fecha.to_period("M")]
    if row.empty:
        return {}
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

def _n(row, col):
    try:
        v = row.get(col)
        return None if v is None or pd.isna(v) else float(v)
    except:
        return None
