import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from utils.config import SHEET_ID, HOJAS, DATE_COLS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

def _get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)

def _leer_hoja(client, sheet_id, nombre_hoja, date_cols=None):
    try:
        sh = client.open_by_key(sheet_id)
        st.write("DEBUG título:", sh.title)
        st.write("DEBUG hojas:", [ws.title for ws in sh.worksheets()])

        ws = sh.worksheet(nombre_hoja)
        data = ws.get_all_values()

        if not data:
            return pd.DataFrame()

        headers = [str(h).strip() for h in data[0]]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)

        if df.empty:
            return df

        if date_cols:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        for col in df.columns:
    if date_cols and col in date_cols:
        continue
    try:
        serie = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace("$", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(".", "", regex=False)   # quita separador de miles
            .str.replace(",", ".", regex=False)  # convierte decimal argentino
        )

        converted = pd.to_numeric(serie, errors="coerce")

        if converted.notna().sum() > len(df) * 0.5:
            df[col] = converted
    except Exception:
        pass

        return df

    except Exception as e:
        st.error(f"Error leyendo hoja '{nombre_hoja}': {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner="Actualizando datos...")
def cargar_datos():
    client = _get_client()
    datos = {}
    for key, nombre in HOJAS.items():
        dcols = DATE_COLS.get(key, [])
        datos[key] = _leer_hoja(client, SHEET_ID, nombre, dcols)
    return datos

def refrescar():
    st.cache_data.clear()
    st.rerun()
