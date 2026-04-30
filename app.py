import streamlit as st
from etl.loader import cargar_datos, refrescar
from utils.config import EMPRESAS, get_colores
from utils.auth import login, logout, get_empresas_permitidas, get_nombre, es_admin
from vistas import resumen, ventas, medios, crm, redes, gestion

st.set_page_config(
    page_title="Dashboard — Gestión Comercial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth ──────────────────────────────────────────────────────────────────────
if not login():
    st.stop()

# ── Empresas permitidas para este usuario ─────────────────────────────────────
empresas_permitidas = get_empresas_permitidas()

# Filtrar solo las que existen en config
empresas_disponibles = [e for e in empresas_permitidas if e in EMPRESAS]

if not empresas_disponibles:
    st.error("Tu usuario no tiene acceso a ninguna empresa. Contactá al administrador.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Saludo
    st.markdown(f"👤 **{get_nombre()}**")
    if es_admin():
        st.caption("🔑 Administrador")
    st.divider()

    # Selector de empresa — solo si tiene acceso a más de una
    if len(empresas_disponibles) > 1:
        st.markdown("### 🏢 Empresa")
        empresa_sel = st.selectbox(
            label="Empresa",
            options=empresas_disponibles,
            key="empresa_sel",
            label_visibility="collapsed",
        )
    else:
        # Solo una empresa — la asigna directo sin mostrar selector
        empresa_sel = empresas_disponibles[0]
        cfg_unica = EMPRESAS[empresa_sel]
        st.markdown(f"### {cfg_unica.get('icono','🏢')} {empresa_sel}")

    cfg_empresa = EMPRESAS[empresa_sel]
    colores     = get_colores(empresa_sel)

    st.divider()
    st.markdown("### ⚙️ Datos")
    if st.button("🔄 Actualizar datos", use_container_width=True,
                 help="Refresca desde Google Sheets"):
        refrescar()

    st.divider()
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        logout()

    st.markdown(
        "<small style='color:#AAA'>Datos con caché de 5 min.</small>",
        unsafe_allow_html=True
    )

# ── Header ────────────────────────────────────────────────────────────────────
icono = cfg_empresa.get("icono", "📊")
color = colores["primario"]
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:8px 0 4px 0">
    <span style="font-size:28px">{icono}</span>
    <div>
        <span style="font-size:22px;font-weight:700;color:{color}">{empresa_sel}</span>
        <span style="font-size:14px;color:#888;margin-left:10px">Dashboard de Marketing</span>
    </div>
</div>
<hr style="margin:6px 0 16px 0;border:none;border-top:2px solid {color}">
""", unsafe_allow_html=True)

# ── Datos ─────────────────────────────────────────────────────────────────────
sheet_id = cfg_empresa["sheet_id"]
with st.spinner(f"Cargando datos de {empresa_sel}..."):
    datos = cargar_datos(sheet_id)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Resumen ejecutivo",
    "💰 Ventas",
    "📣 Inversión y medios",
    "🎯 CRM y embudo",
    "📱 Redes",
    "⚙️ Gestión",
])

with tab1: resumen.render(datos, colores)
with tab2: ventas.render(datos, colores, empresa_sel)
with tab3: medios.render(datos, colores)
with tab4: crm.render(datos, colores)
with tab5: redes.render(datos, colores)
with tab6: gestion.render(datos, colores)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:#CCC;font-size:12px;margin-top:40px;
            padding-top:16px;border-top:1px solid #EEE">
    {empresa_sel} — Sistema de Marketing Inteligente
</div>""", unsafe_allow_html=True)
