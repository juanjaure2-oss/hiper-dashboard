import pandas as pd

def kpi_mes(df_kpi: pd.DataFrame, fecha: pd.Timestamp) -> dict:
    """Retorna todos los KPIs de un mes específico."""
    row = df_kpi[df_kpi["fecha"].dt.to_period("M") == fecha.to_period("M")]
    if row.empty:
        return {}
    r = row.iloc[0]
    return {
        "fecha":                   r.get("fecha"),
        "ventas":                  _n(r, "ventas"),
        "inversion_medios":        _n(r, "inversion_medios"),
        "otros_gastos_mkt":        _n(r, "otros_gastos_mkt"),
        "presupuesto_total":       _n(r, "presupuesto_total"),
        "ratio_presupuesto_ventas":_n(r, "ratio_presupuesto_ventas"),
        "leads_validados":         _n(r, "leads_validados"),
        "clientes_nuevos":         _n(r, "clientes_nuevos"),
    }

def ultimo_mes(df_kpi: pd.DataFrame) -> pd.Timestamp:
    df = df_kpi.dropna(subset=["ventas"])
    if df.empty:
        return None
    return df["fecha"].max()

def mes_anterior(df_kpi: pd.DataFrame, fecha: pd.Timestamp) -> dict:
    mes_ant = fecha - pd.DateOffset(months=1)
    return kpi_mes(df_kpi, mes_ant)

def variacion_pct(actual, anterior):
    try:
        a, b = float(actual), float(anterior)
        if b == 0:
            return None
        return (a - b) / abs(b)
    except:
        return None

def _n(row, col):
    try:
        v = row.get(col)
        if v is None or pd.isna(v):
            return None
        return float(v)
    except:
        return None
