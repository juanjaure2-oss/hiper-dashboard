import streamlit as st
from etl.loader import cargar_datos, refrescar
from vistas import resumen, ventas, medios, crm, redes, gestion

st.set_page_config(
    page_title="Hiper Argentina — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auth simple ───────────────────────────────────────────
def check_password():
    if "autenticado" in st.session_state and st.session_state["autenticado"]:
        return True
    st.markdown("""
    <div style="max-width:380px;margin:80px auto;text-align:center">
        <img src="https://i.imgur.com/placeholder.png" width="120" style="display:none">
        <h2 style="color:#1F3864;margin-bottom:4px">Hiper Argentina</h2>
        <p style="color:#666;margin-bottom:28px">Dashboard de Marketing</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
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

# ── Header ────────────────────────────────────────────────
col_logo, col_title, col_btn = st.columns([1, 6, 1])
with col_title:
    st.markdown("""
    <div style="padding:8px 0">
        <span style="font-size:22px;font-weight:700;color:#1F3864">📊 Hiper Argentina</span>
        <span style="font-size:14px;color:#888;margin-left:12px">Dashboard de Marketing</span>
    </div>
    """, unsafe_allow_html=True)
with col_btn:
    if st.button("🔄 Actualizar", help="Refresca los datos desde Google Sheets"):
        refrescar()

st.markdown('<hr style="margin:0 0 16px 0;border:none;border-top:1px solid #EEE">', unsafe_allow_html=True)

# ── Carga de datos ────────────────────────────────────────
with st.spinner("Cargando datos..."):
    datos = cargar_datos()

# ── Tabs ─────────────────────────────────────────────────
TABS = [
    "📋 Resumen ejecutivo",
    "💰 Ventas",
    "📣 Inversión y medios",
    "🎯 CRM y embudo",
    "📱 Redes",
    "⚙️ Gestión",
]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(TABS)

with tab1:
    resumen.render(datos)
with tab2:
    ventas.render(datos)
with tab3:
    medios.render(datos)
with tab4:
    crm.render(datos)
with tab5:
    redes.render(datos)
with tab6:
    gestion.render(datos)

# ── Footer ────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#CCC;font-size:12px;margin-top:40px;padding-top:16px;border-top:1px solid #EEE">
    Hiper Argentina — Sistema de Marketing Inteligente
</div>
""", unsafe_allow_html=True)
