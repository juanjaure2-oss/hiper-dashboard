import pandas as pd

def ars(valor, decimales=0):
    if valor is None or pd.isna(valor):
        return "—"
    try:
        v = float(valor)
        if abs(v) >= 1_000_000:
            return f"$ {v/1_000_000:.1f}M"
        if abs(v) >= 1_000:
            return f"$ {v/1_000:.0f}K"
        return f"$ {v:,.{decimales}f}"
    except:
        return "—"

def pct(valor, decimales=1):
    if valor is None or pd.isna(valor):
        return "—"
    try:
        return f"{float(valor)*100:.{decimales}f}%"
    except:
        return "—"

def num(valor, decimales=0):
    if valor is None or pd.isna(valor):
        return "—"
    try:
        return f"{float(valor):,.{decimales}f}"
    except:
        return "—"

def variacion(actual, anterior):
    if actual is None or anterior is None:
        return None, "—"
    try:
        a, b = float(actual), float(anterior)
        if b == 0:
            return None, "—"
        v = (a - b) / abs(b)
        signo = "▲" if v >= 0 else "▼"
        color = "green" if v >= 0 else "red"
        return v, f"{signo} {abs(v)*100:.1f}%"
    except:
        return None, "—"

def periodo_label(fecha):
    try:
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        return f"{meses[fecha.month-1]} {fecha.year}"
    except:
        return str(fecha)
