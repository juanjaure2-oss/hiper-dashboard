SHEET_ID = "1dbiyQ3uox69Xd-3G3Z5apamM0Ut6S04g"

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

COLORES = {
    "primario":    "#C0392B",
    "secundario":  "#1F3864",
    "acento":      "#E8F5E9",
    "google":      "#4285F4",
    "meta":        "#1877F2",
    "positivo":    "#27AE60",
    "negativo":    "#E74C3C",
    "neutro":      "#7F8C8D",
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
