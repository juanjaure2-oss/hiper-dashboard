import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import num, periodo_label
from utils.config import COLORES

CANAL_COLORES = {
    "facebook":  "#1877F2",
    "instagram": "#E1306C",
    "linkedin":  "#0A66C2",
}

def render(datos: dict):
    df_r = datos.get("redes", pd.DataFrame())
    if df_r.empty:
        st.warning("Sin datos de redes.")
        return

    df_r = df_r.copy()
    df_r["fecha"] = pd.to_datetime(df_r["fecha"], errors="coerce")
    df_r = df_r.dropna(subset=["fecha"])
    df_r["canal"] = df_r["canal"].str.lower().str.strip()
    df_r["periodo"] = df_r["fecha"].dt.to_period("M")

    periodos = sorted(df_r["periodo"].unique(), reverse=True)
    sel = st.selectbox("Período", [str(p) for p in periodos], index=0, key="redes_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    df_mes = df_r[df_r["periodo"] == periodo_sel]
    st.divider()

    # Métricas por canal
    canales = ["facebook","instagram","linkedin"]
    cols = st.columns(len(canales))

    for i, canal in enumerate(canales):
        d = df_mes[df_mes["canal"] == canal]
        with cols[i]:
            nombre = canal.capitalize()
            color = CANAL_COLORES.get(canal, COLORES["secundario"])
            if d.empty:
                st.markdown(f"""
                <div style="background:#F8F9FA;border-radius:10px;padding:14px;border-top:4px solid {color}">
                    <div style="font-weight:600;color:{color};margin-bottom:8px">{nombre}</div>
                    <div style="color:#999;font-size:13px">Sin datos</div>
                </div>""", unsafe_allow_html=True)
            else:
                row = d.iloc[0]
                st.markdown(f"""
                <div style="background:#F8F9FA;border-radius:10px;padding:14px;border-top:4px solid {color}">
                    <div style="font-weight:600;color:{color};margin-bottom:10px">{nombre}</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:13px">
                        <div><span style="color:#666">Seguidores</span><br><b>{num(row.get('seguidores_totales',0))}</b></div>
                        <div><span style="color:#666">Adquiridos</span><br><b>+{num(row.get('adquiridos',0))}</b></div>
                        <div><span style="color:#666">Impresiones</span><br><b>{num(row.get('impresiones',0))}</b></div>
                        <div><span style="color:#666">Interacciones</span><br><b>{num(row.get('interacciones',0))}</b></div>
                        <div><span style="color:#666">Contenidos</span><br><b>{num(row.get('cantidad_contenido',0))}</b></div>
                    </div>
                </div>""", unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Seguidores", "Impresiones", "Interacciones"])

    def grafico_evolucion(metrica, titulo):
        fig = go.Figure()
        for canal in canales:
            df_canal = df_r[df_r["canal"] == canal].sort_values("periodo")
            if df_canal.empty or metrica not in df_canal.columns:
                continue
            df_canal["label"] = df_canal["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))
            fig.add_trace(go.Scatter(
                x=df_canal["label"], y=df_canal[metrica],
                name=canal.capitalize(), mode="lines+markers",
                line=dict(color=CANAL_COLORES.get(canal, "#999"), width=2),
                marker=dict(size=6),
                hovertemplate=f"<b>%{{x}}</b><br>{canal.capitalize()}: %{{y:,.0f}}<extra></extra>"
            ))
        fig.update_layout(
            height=300, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        return fig

    with tab1:
        st.plotly_chart(grafico_evolucion("seguidores_totales", "Seguidores"), use_container_width=True)
    with tab2:
        st.plotly_chart(grafico_evolucion("impresiones", "Impresiones"), use_container_width=True)
    with tab3:
        st.plotly_chart(grafico_evolucion("interacciones", "Interacciones"), use_container_width=True)

    # Contenido producido
    st.divider()
    st.markdown("##### Contenido publicado por mes")
    df_cont = df_r.groupby(["periodo","canal"])["cantidad_contenido"].sum().reset_index()
    df_cont["label"] = df_cont["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))
    fig_cont = go.Figure()
    for canal in canales:
        d = df_cont[df_cont["canal"] == canal].sort_values("periodo")
        if d.empty: continue
        fig_cont.add_trace(go.Bar(
            x=d["label"], y=d["cantidad_contenido"],
            name=canal.capitalize(),
            marker_color=CANAL_COLORES.get(canal, "#999"),
            hovertemplate=f"<b>%{{x}}</b><br>{canal.capitalize()}: %{{y}} piezas<extra></extra>"
        ))
    fig_cont.update_layout(
        barmode="group", height=260,
        margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#EEE"),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_cont, use_container_width=True)
