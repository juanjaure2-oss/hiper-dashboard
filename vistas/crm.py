import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import num, periodo_label, variacion
from utils.config import COLORES


ORDEN_EMBUDO = [
    "cliente activo",
    "en oportunidad (cotizando)",
    "lead templado (scoring - no usar factibilidad))",
    "lead caliente (scoring - no usar factibilidad))",
    "lead frío (dato sin calificación)",
    "lead sin contacto (se llamó 5 días diferentes)",
    "lead perdido (automático)",
    "cliente perdido (especificar motivo)",
    "otro descartado (no califica)",
]

LABELS_CORTOS = {
    "cliente activo": "Cliente activo",
    "en oportunidad (cotizando)": "En oportunidad",
    "lead templado (scoring - no usar factibilidad))": "Lead templado",
    "lead caliente (scoring - no usar factibilidad))": "Lead caliente",
    "lead frío (dato sin calificación)": "Lead frío",
    "lead sin contacto (se llamó 5 días diferentes)": "Sin contacto",
    "lead perdido (automático)": "Lead perdido",
    "cliente perdido (especificar motivo)": "Cliente perdido",
    "otro descartado (no califica)": "Descartado",
}


def _safe_text(s):
    return (
        s.astype(str)
        .str.strip()
        .replace(
            {
                "": None,
                "nan": None,
                "None": None,
                "0": "Desconocido",
                "-": "Desconocido",
            }
        )
    )
