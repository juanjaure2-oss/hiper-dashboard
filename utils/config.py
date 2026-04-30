EMPRESAS = {
    "Hiper Argentina": {
        "sheet_id":      "1dbiyQ3uox69Xd-3G3Z5apamM0Ut6S04g",
        "color_primario": "#C0392B",
        "icono":         "🏭",
        "lineas_venta":  ["zingueria", "perfileria"],
        "labels_venta":  ["Zinguería", "Perfilería"],
    },
    "Abasto": {
        "sheet_id":      "SHEET_ID_ABASTO",
        "color_primario": "#1A6B3C",
        "icono":         "🏪",
        "lineas_venta":  [],
        "labels_venta":  [],
    },
    "G Tec": {
        "sheet_id":      "SHEET_ID_GTEC",
        "color_primario": "#1F4E8C",
        "icono":         "⚙️",
        "lineas_venta":  [],
        "labels_venta":  [],
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
    "secundario": "#1F3864",
    "acento":     "#E8F5E9",
    "google":     "#4285F4",
    "meta":       "#1877F2",
    "positivo":   "#27AE60",
    "negativo":   "#E74C3C",
    "neutro":     "#7F8C8D",
}

def get_colores(empresa: str) -> dict:
    cfg = EMPRESAS.get(empresa, {})
    return {**COLORES_BASE, "primario": cfg.get("color_primario", "#C0392B")}

def get_lineas_venta(empresa: str):
    cfg = EMPRESAS.get(empresa, {})
    return cfg.get("lineas_venta", []), cfg.get("labels_venta", [])
