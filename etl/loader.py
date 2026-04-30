import time
import streamlit as st
import gspread
import pandas as pd
import numpy as np
from google.oauth2.service_account import Credentials
from utils.config import HOJAS, DATE_COLS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

NUMERIC_COLS = {
    "kpi":         ["ventas","inversion_medios","otros_gastos_mkt","presupuesto_total",
                    "ratio_presupuesto_ventas","leads_validados","clientes_nuevos"],
    "ventas":      ["cantidad","zingueria","perfileria","total"],
    "presupuesto": ["asesor_mkt","analista_comercial","agencia","inversiones","total_otros_gastos"],
    "leads":       ["cantidad"],
    "redes":       ["seguidores_totales","adquiridos","impresiones","interacciones","cantidad_contenido"],
    "piezas":      ["cantidad"],
    "ads":         ["impresiones","clics","ctr","conversiones","costo","cpc","costo_por_conversion"],
    "crm":         ["lead_scoring"],
    "tareas":      [],
    "reuniones":   [],
}

MESES_ES = {
    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
    "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
}

def _parse_num(val):
    if val is None or val == "": return np.nan
    if isinstance(val, (int, float)):
        return float(val) if not (isinstance(val, float) and np.isnan(val)) else np.nan
    s = str(val).strip().replace("$","").replace(" ","")
    if s in ("","-","N/A","n/a","#N/A","#VALUE!"): return np.nan
    if "," in s: s = s.replace(".","").replace(",",".")
    elif s.count(".") > 1: s = s.replace(".","")
    try: return float(s)
    except: return np.nan

def _parse_date(val, _anio_ref=[None]):
    """
    Convierte fechas en cualquier formato incluyendo nombres de meses en español.
    _anio_ref es una lista mutable que mantiene el año inferido entre llamadas
    para secuencias como Enero, Febrero... Enero 2026.
    """
    if val is None or val == "": return pd.NaT

    # Número serial de Google Sheets
    if isinstance(val, (int, float)):
        if isinstance(val, float) and np.isnan(val): return pd.NaT
        try: return pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(val))
        except: return pd.NaT

    s = str(val).strip()
    if s in ("","N/A","#N/A","#VALUE!"): return pd.NaT

    # Intentar formatos estándar primero
    formatos = ["%Y-%m-%d","%d/%m/%Y","%m/%d/%Y","%d-%m-%Y","%Y/%m/%d","%d/%m/%y"]
    for fmt in formatos:
        try: return pd.to_datetime(s, format=fmt)
        except: continue

    # Nombres de meses en español: "Enero", "enero 2026", "Febrero 2026"
    parts = s.lower().split()
    if parts and parts[0] in MESES_ES:
        mes = MESES_ES[parts[0]]
        if len(parts) > 1 and parts[1].isdigit():
            anio = int(parts[1])
            _anio_ref[0] = anio
        else:
            # Sin año explícito — inferir año base 2025
            # Si el mes es enero y ya vimos diciembre, subir el año
            if _anio_ref[0] is None:
                _anio_ref[0] = 2025
            anio = _anio_ref[0]
        try:
            return pd.Timestamp(year=anio, month=mes, day=1)
        except:
            return pd.NaT

    # Fallback general
    try: return pd.to_datetime(s, dayfirst=True, errors="coerce")
    except: return pd.NaT

def _parse_date_col(series: pd.Series) -> pd.Series:
    """Parsea una columna completa de fechas con contexto de año."""
    anio_ref = [None]
    result = []
    for val in series:
        # Usar closure con anio_ref mutable
        if val is None or val == "":
            result.append(pd.NaT)
            continue
        if isinstance(val, (int, float)):
            if isinstance(val, float) and np.isnan(val):
                result.append(pd.NaT)
                continue
            try:
                result.append(pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(val)))
            except:
                result.append(pd.NaT)
            continue

        s = str(val).strip()
        if s in ("","N/A","#N/A","#VALUE!"):
            result.append(pd.NaT)
            continue

        # Formatos estándar
        parsed = pd.NaT
        for fmt in ["%Y-%m-%d","%d/%m/%Y","%m/%d/%Y","%d-%m-%Y","%Y/%m/%d","%d/%m/%y"]:
            try:
                parsed = pd.to_datetime(s, format=fmt)
                break
            except:
                continue

        if pd.isna(parsed):
            # Nombres de meses en español
            parts = s.lower().split()
            if parts and parts[0] in MESES_ES:
                mes = MESES_ES[parts[0]]
                if len(parts) > 1 and parts[1].isdigit():
                    anio_ref[0] = int(parts[1])
                else:
                    if anio_ref[0] is None:
                        anio_ref[0] = 2025
                    # Si volvemos a enero y ya pasamos por meses altos, subir año
                    if mes == 1 and len(result) > 0:
                        last_valid = next((r for r in reversed(result) if pd.notna(r)), None)
                        if last_valid and last_valid.month >= 11:
                            anio_ref[0] = last_valid.year + 1
                try:
                    parsed = pd.Timestamp(year=anio_ref[0], month=mes, day=1)
                except:
                    parsed = pd.NaT
            else:
                try:
                    parsed = pd.to_datetime(s, dayfirst=True, errors="coerce")
                except:
                    parsed = pd.NaT

        if pd.notna(parsed) and anio_ref[0] is None:
            anio_ref[0] = parsed.year

        result.append(parsed)

    return pd.Series(result, index=series.index)

def _get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

def _leer_hoja(client, sheet_id: str, key: str, nombre_hoja: str, date_cols: list) -> pd.DataFrame:
    for intento in range(3):
        try:
            ws = client.open_by_key(sheet_id).worksheet(nombre_hoja)
            data = ws.get_all_records(
                numericise_ignore=["all"],
                value_render_option="UNFORMATTED_VALUE"
            )
            df = pd.DataFrame(data)
            if df.empty:
                return df

            df.columns = [c.strip() for c in df.columns]

            # Convertir fechas con parser inteligente
            for col in date_cols:
                if col in df.columns:
                    df[col] = _parse_date_col(df[col])

            # Convertir numéricos
            for col in NUMERIC_COLS.get(key, []):
                if col in df.columns:
                    df[col] = df[col].apply(_parse_num)

            return df

        except gspread.exceptions.WorksheetNotFound:
            return pd.DataFrame()
        except gspread.exceptions.APIError as e:
            if "429" in str(e) and intento < 2:
                time.sleep(3 + intento * 3)
                continue
            st.warning(f"⚠️ No se pudo leer '{nombre_hoja}': {e}")
            return pd.DataFrame()
        except Exception as e:
            st.warning(f"⚠️ No se pudo leer '{nombre_hoja}': {e}")
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner="Cargando datos...")
def cargar_datos(sheet_id: str) -> dict:
    client = _get_client()
    datos = {}
    for key, nombre in HOJAS.items():
        dcols = DATE_COLS.get(key, [])
        datos[key] = _leer_hoja(client, sheet_id, key, nombre, dcols)
        time.sleep(0.3)
    return datos

def refrescar():
    st.cache_data.clear()
    st.rerun()
