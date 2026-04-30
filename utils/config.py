# ─── EMPRESAS ────────────────────────────────────────────────────────────────
# Para agregar una empresa nueva: sumar una entrada a este dict con su Sheet ID.
# No hay que tocar ningún otro archivo.

EMPRESAS = {
    "Hiper Argentina": {
        "sheet_id": "1dbiyQ3uox69Xd-3G3Z5apamM0Ut6S04g",
        "color_primario": "#C0392B",
        "icono": "🏭",
    },
    "Abasto": {
        "sheet_id": "SHEET_ID_ABASTO",   # reemplazar cuando esté disponible
        "color_primario": "#1A6B3C",
        "icono": "🏪",
    },
    "G Tec": {
        "sheet_id": "SHEET_ID_GTEC",     # reemplazar cuando esté disponible
        "color_primario": "#1F4E8C",
        "icono": "⚙️",
    },
}

# ─── HOJAS (iguales para todas las empresas) ─────────────────────────────────
HOJAS = {
    "kpi":        "kpi_historico",
    "ventas":     "ventas",
    "presupuesto":"presupuesto",
    "leads":      "leads_validados",
    "redes":      "redes",
    "piezas":     "piezas",
    "reuniones":  "reuniones",
    "ads":        "ads_mensual",
    "crm":        "crm_resumen",
    "tareas":     "proyectos_tareas",
}

# ─── COLUMNAS DE FECHA por hoja ───────────────────────────────────────────────
DATE_COLS = {
    "kpi":         ["fecha"],
    "ventas":      ["fecha"],
    "presupuesto": ["fecha"],
    "leads":       ["fecha"],
    "redes":       ["fecha"],
    "piezas":      ["fecha"],
    "reuniones":   ["fecha"],
    "ads":         ["fecha"],
    "crm":         ["fecha_creado", "ultimo_contacto", "fecha_ultima_compra"],
    "tareas":      ["fecha_inicio", "fecha_vencimiento"],
}

# ─── COLORES BASE (se sobreescriben por empresa) ──────────────────────────────
COLORES_BASE = {
    "secundario":  "#1F3864",
    "acento":      "#E8F5E9",
    "google":      "#4285F4",
    "meta":        "#1877F2",
    "positivo":    "#27AE60",
    "negativo":    "#E74C3C",
    "neutro":      "#7F8C8D",
}

def get_colores(empresa: str) -> dict:
    """Retorna el dict de colores completo para una empresa."""
    cfg = EMPRESAS.get(empresa, {})
    return {
        **COLORES_BASE,
        "primario": cfg.get("color_primario", "#C0392B"),
    }
