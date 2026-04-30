import streamlit as st
from etl.loader import cargar_datos, refrescar
from utils.config import EMPRESAS, get_colores
from vistas import resumen, ventas, medios, crm, redes, gestion

st.set_page_config(
    page_title="Dashboard — Gestión Comercial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

def check_password():
    if st.session_state.get("autenticado"):
        return True
    st.markdown("""
    <div style="max-width:380px;margin:80px auto;text-align:center">
        <h2 style="color:#1F3864;margin-bottom:4px">Dashboard Comercial</h2>
        <p style="color:#666;margin-bottom:28px">Ingresá tu contraseña para continuar</p>
    </div>""", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        pwd = st.text_input("Contraseña", type="password", key="pwd_input")
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if pwd == st.secrets.get("dashboard_password", "hiper2025"):
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    return False

if not check_password():
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("### 🏢 Empresa")
    empresa_sel = st.selectbox(
        label="Seleccioná la empresa",
        options=list(EMPRESAS.keys()),
        key="empresa_sel",
        label_visibility="collapsed",
    )
    cfg_empresa = EMPRESAS[empresa_sel]
    colores     = get_colores(empresa_sel)
    st.divider()
    st.markdown("### ⚙️ Datos")
    if st.button("🔄 Actualizar datos", use_container_width=True):
        refrescar()
    st.divider()
    st.markdown(
        "<small style='color:#AAA'>Datos con caché de 5 min.</small>",
        unsafe_allow_html=True
    )

# Header
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

# Datos
sheet_id = cfg_empresa["sheet_id"]
with st.spinner(f"Cargando datos de {empresa_sel}..."):
    datos = cargar_datos(sheet_id)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Resumen ejecutivo",
    "💰 Ventas",
    "📣 Inversión y medios",
    "🎯 CRM y embudo",
    "📱 Redes",
    "⚙️ Gestión",
])

with tab1: resumen.render(datos, colores)
with tab2: ventas.render(datos, colores)
with tab3: medios.render(datos, colores)
with tab4: crm.render(datos, colores)
with tab5: redes.render(datos, colores)
with tab6: gestion.render(datos, colores)

st.markdown(f"""
<div style="text-align:center;color:#CCC;font-size:12px;margin-top:40px;
            padding-top:16px;border-top:1px solid #EEE">
    {empresa_sel} — Sistema de Marketing Inteligente
</div>""", unsafe_allow_html=True)
