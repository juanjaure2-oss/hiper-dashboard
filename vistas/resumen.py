import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from etl.kpi import ultimo_mes, kpi_mes, mes_anterior, variacion_pct
from utils.formato import ars, pct, num, periodo_label
from utils.config import COLORES

def _metrica(label, valor_fmt, delta_txt, delta_val):
    color = COLORES["positivo"] if delta_val and delta_val >= 0 else COLORES["negativo"]
    icono = "▲" if delta_val and delta_val >= 0 else "▼"
    delta_html = f'<span style="color:{color};font-size:13px">{icono} {delta_txt}</span>' if delta_txt and delta_txt != "—" else ""
    st.markdown(f"""
    <div style="background:#F8F9FA;border-radius:10px;padding:16px 18px;border-left:4px solid {COLORES['secundario']}">
        <div style="font-size:12px;color:#666;margin-bottom:4px">{label}</div>
        <div style="font-size:24px;font-weight:600;color:{COLORES['secundario']}">{valor_fmt}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def render(datos: dict):
    df_kpi = datos.get("kpi", pd.DataFrame())
    if df_kpi.empty:
        st.warning("Sin datos de KPI histórico.")
        return

    ult = ultimo_mes(df_kpi)
    if ult is None:
        st.warning("Sin datos disponibles.")
        return

    actual = kpi_mes(df_kpi, ult)
    anterior = mes_anterior(df_kpi, ult)

    # Header
    st.markdown(f"### Resumen ejecutivo — {periodo_label(ult)}")
    st.caption("Comparado con el mes anterior")
    st.divider()

    # Fila 1: métricas principales
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        v = actual.get("ventas")
        vp = anterior.get("ventas")
        dv = variacion_pct(v, vp)
        _metrica("Ventas del período", ars(v), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)
    with c2:
        v = actual.get("inversion_medios")
        vp = anterior.get("inversion_medios")
        dv = variacion_pct(v, vp)
        _metrica("Inversión en medios", ars(v), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)
    with c3:
        v = actual.get("presupuesto_total")
        vp = anterior.get("presupuesto_total")
        dv = variacion_pct(v, vp)
        _metrica("Presupuesto total MKT", ars(v), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)
    with c4:
        v = actual.get("leads_validados")
        vp = anterior.get("leads_validados")
        dv = variacion_pct(v, vp)
        _metrica("Leads validados", num(v), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # Fila 2: métricas secundarias
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        v = actual.get("otros_gastos_mkt")
        vp = anterior.get("otros_gastos_mkt")
        dv = variacion_pct(v, vp)
        _metrica("Otros gastos MKT", ars(v), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)
    with c2:
        v = actual.get("ratio_presupuesto_ventas")
        vp = anterior.get("ratio_presupuesto_ventas")
        dv = variacion_pct(v, vp)
        _metrica("Ratio presupuesto/ventas", pct(v), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)
    with c3:
        inv = actual.get("inversion_medios")
        leads = actual.get("leads_validados")
        cpl = (inv / leads) if inv and leads and leads > 0 else None
        inv_p = anterior.get("inversion_medios")
        leads_p = anterior.get("leads_validados")
        cpl_p = (inv_p / leads_p) if inv_p and leads_p and leads_p > 0 else None
        dv = variacion_pct(cpl, cpl_p)
        _metrica("Costo por lead", ars(cpl), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)
    with c4:
        v = actual.get("clientes_nuevos")
        vp = anterior.get("clientes_nuevos")
        dv = variacion_pct(v, vp)
        _metrica("Clientes nuevos", num(v), f"{abs(dv)*100:.1f}%" if dv is not None else "—", dv)

    st.divider()

    # Gráfico evolución histórica
    st.markdown("##### Evolución histórica")
    df_plot = df_kpi.dropna(subset=["ventas"]).copy()
    df_plot["label"] = df_plot["fecha"].apply(periodo_label)

    tab1, tab2, tab3 = st.tabs(["Ventas", "Inversión vs Presupuesto", "Leads validados"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_plot["label"], y=df_plot["ventas"],
            mode="lines+markers", name="Ventas",
            line=dict(color=COLORES["primario"], width=2),
            marker=dict(size=5),
            hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>"
        ))
        fig.update_layout(
            height=320, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            xaxis=dict(gridcolor="#EEE", tickangle=-45),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_p = df_kpi.dropna(subset=["inversion_medios","presupuesto_total"]).copy()
        df_p["label"] = df_p["fecha"].apply(periodo_label)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_p["label"], y=df_p["inversion_medios"],
            name="Inversión medios", marker_color=COLORES["google"],
            hovertemplate="<b>%{x}</b><br>Inv. medios: $%{y:,.0f}<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=df_p["label"], y=df_p["otros_gastos_mkt"],
            name="Otros gastos", marker_color=COLORES["secundario"],
            hovertemplate="<b>%{x}</b><br>Otros gastos: $%{y:,.0f}<extra></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=df_p["label"], y=df_p["ventas"],
            name="Ventas", mode="lines",
            line=dict(color=COLORES["primario"], width=2, dash="dot"),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>"
        ))
        fig.update_layout(
            barmode="stack", height=320,
            margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            yaxis2=dict(tickformat="$,.0f", overlaying="y", side="right", showgrid=False),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        df_l = df_kpi.dropna(subset=["leads_validados"]).copy()
        df_l["label"] = df_l["fecha"].apply(periodo_label)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_l["label"], y=df_l["leads_validados"],
            marker_color=COLORES["positivo"],
            hovertemplate="<b>%{x}</b><br>Leads: %{y:,.0f}<extra></extra>"
        ))
        fig.update_layout(
            height=320, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
