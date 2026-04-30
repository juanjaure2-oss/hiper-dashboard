import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from utils.config import HOJAS, DATE_COLS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

def _get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

def _leer_hoja(client, sheet_id: str, nombre_hoja: str, date_cols: list) -> pd.DataFrame:
    try:
        ws = client.open_by_key(sheet_id).worksheet(nombre_hoja)
        data = ws.get_all_records(numericise_ignore=["all"])
        df = pd.DataFrame(data)
        if df.empty:
            return df
        df.columns = [c.strip() for c in df.columns]
        # Convert dates
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        return df
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"⚠️ No se pudo leer '{nombre_hoja}': {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner="Cargando datos...")
def cargar_datos(sheet_id: str) -> dict:
    client = _get_client()
    datos = {}
    for key, nombre in HOJAS.items():
        dcols = DATE_COLS.get(key, [])
        datos[key] = _leer_hoja(client, sheet_id, nombre, dcols)
    return datos

def refrescar():
    st.cache_data.clear()
    st.rerun()
