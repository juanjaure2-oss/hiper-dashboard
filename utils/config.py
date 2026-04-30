EMPRESAS = {
    "Hiper Argentina": {
        "sheet_id": "1dbiyQ3uox69Xd-3G3Z5apamM0Ut6S04g",
        "color_primario": "#C0392B",
        "icono": "🏭",
    },
    "Abasto": {
        "sheet_id": "1zwsH8Dsmlwhd9lbTWhlSO1FDKzjwT297K9MndCMd5Tw",
        "color_primario": "#1A6B3C",
        "icono": "🏪",
    },
    "G Tec": {
        "sheet_id": "1Ursnaw6l0dlC5fhKI4i5yRZE2ex1PrPwfrTE_pk_KFs",
        "color_primario": "#1F4E8C",
        "icono": "⚙️",
    },
}

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
    cfg = EMPRESAS.get(empresa, {})
    return {
        **COLORES_BASE,
        "primario": cfg.get("color_primario", "#C0392B"),
    }
