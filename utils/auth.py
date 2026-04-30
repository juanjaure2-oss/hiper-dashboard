import streamlit as st
import bcrypt

def _verificar_password(password_ingresada: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(
            password_ingresada.encode(),
            hash_guardado.encode()
        )
    except:
        return False

def login():
    """
    Muestra pantalla de login y maneja la sesión.
    Retorna True si el usuario está autenticado.
    """
    if st.session_state.get("autenticado"):
        return True

    # Pantalla de login
    st.markdown("""
    <div style="max-width:420px;margin:60px auto 0 auto">
        <div style="text-align:center;margin-bottom:32px">
            <div style="font-size:40px;margin-bottom:8px">📊</div>
            <h2 style="color:#1F3864;margin:0">Dashboard Comercial</h2>
            <p style="color:#888;margin-top:6px">Ingresá tus credenciales para continuar</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login_form"):
            usuario = st.text_input("Usuario", placeholder="tu usuario").strip().lower()
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

        if submitted:
            usuarios = st.secrets.get("usuarios", {})
            if usuario in usuarios:
                cfg = usuarios[usuario]
                if _verificar_password(password, cfg["password"]):
                    st.session_state["autenticado"]  = True
                    st.session_state["usuario"]      = usuario
                    st.session_state["nombre"]       = cfg.get("nombre", usuario)
                    st.session_state["empresas"]     = list(cfg.get("empresas", []))
                    st.session_state["rol"]          = cfg.get("rol", "viewer")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
            else:
                st.error("Usuario no encontrado")

    return False

def logout():
    for key in ["autenticado","usuario","nombre","empresas","rol"]:
        st.session_state.pop(key, None)
    st.rerun()

def get_empresas_permitidas() -> list:
    return st.session_state.get("empresas", [])

def get_nombre() -> str:
    return st.session_state.get("nombre", "")

def get_rol() -> str:
    return st.session_state.get("rol", "viewer")

def es_admin() -> bool:
    return get_rol() == "admin"
