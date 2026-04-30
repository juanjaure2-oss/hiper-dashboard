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

def _parse_num(val):
    """Convierte cualquier valor a float. Maneja formato ARS."""
    if val is None or val == "":
        return np.nan
    if isinstance(val, (int, float)):
        return float(val) if not (isinstance(val, float) and np.isnan(val)) else np.nan
    s = str(val).strip()
    if s in ("", "-", "N/A", "n/a", "#N/A", "#VALUE!"):
        return np.nan
    s = s.replace("$", "").replace(" ", "").replace("%", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        parts = s.split(".")
        if len(parts) > 2:
            s = s.replace(".", "")
    try:
        return float(s)
    except:
        return np.nan

def _parse_date(val):
    """
    Convierte fechas que pueden venir como:
    - string "01/06/2025" o "2025-06-01"
    - número serial de Excel/Sheets (ej: 46073)
    - ya timestamp
    """
    if val is None or val == "":
        return pd.NaT
    # Si es número (serial de Sheets con UNFORMATTED_VALUE)
    if isinstance(val, (int, float)):
        if np.isnan(val) if isinstance(val, float) else False:
            return pd.NaT
        # Sheets usa epoch 30/12/1899 (igual que Excel)
        try:
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(val))
        except:
            return pd.NaT
    # Si es string
    s = str(val).strip()
    if s in ("", "N/A", "#N/A"):
        return pd.NaT
    # Try multiple formats
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
        try:
            return pd.to_datetime(s, format=fmt)
        except:
            continue
    # Fallback
    try:
        return pd.to_datetime(s, dayfirst=True, errors="coerce")
    except:
        return pd.NaT

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

            # Convert date columns
            for col in date_cols:
                if col in df.columns:
                    df[col] = df[col].apply(_parse_date)

            # Convert numeric columns
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
