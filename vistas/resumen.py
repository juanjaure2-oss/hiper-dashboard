import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from etl.kpi import ultimo_mes, kpi_mes, mes_anterior, variacion_pct
from utils.formato import ars, pct, num, periodo_label

def _n(val):
    try:
        return float(str(val).replace(',','.').replace('$','').replace('%','').strip())
    except:
        return None

def _metrica(label, valor_fmt, delta_txt, delta_val, colores):
    color = colores["positivo"] if delta_val and delta_val >= 0 else colores["negativo"]
    icono = "▲" if delta_val and delta_val >= 0 else "▼"
    delta_html = (
        f'<span style="color:{color};font-size:13px">{icono} {delta_txt}</span>'
        if delta_txt and delta_txt != "—" else ""
    )
    st.markdown(f"""
    <div style="background:#F8F9FA;border-radius:10px;padding:16px 18px;
                border-left:4px solid {colores['secundario']}">
        <div style="font-size:12px;color:#666;margin-bottom:4px">{label}</div>
        <div style="font-size:24px;font-weight:600;color:{colores['secundario']}">{valor_fmt}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

def render(datos: dict, colores: dict):
    df_kpi = datos.get("kpi", pd.DataFrame())
    if df_kpi.empty:
        st.warning("Sin datos de KPI histórico.")
        return

    # Force numeric columns
    df_kpi = df_kpi.copy()
    df_kpi["fecha"] = pd.to_datetime(df_kpi["fecha"], errors="coerce")
    for col in ["ventas","inversion_medios","otros_gastos_mkt","presupuesto_total",
                "ratio_presupuesto_ventas","leads_validados","clientes_nuevos"]:
        if col in df_kpi.columns:
            df_kpi[col] = pd.to_numeric(
                df_kpi[col].astype(str).str.replace(',','.').str.replace('$','').str.replace('%','').str.strip(),
                errors="coerce"
            )

    ult = ultimo_mes(df_kpi)
    if ult is None:
        st.warning("Sin datos disponibles.")
        return

    actual   = kpi_mes(df_kpi, ult)
    anterior = mes_anterior(df_kpi, ult)

    st.markdown(f"### Resumen ejecutivo — {periodo_label(ult)}")
    st.caption("Comparado con el mes anterior")
    st.divider()

    def delta(key):
        v, vp = actual.get(key), anterior.get(key)
        d = variacion_pct(v, vp)
        return d, f"{abs(d)*100:.1f}%" if d is not None else "—"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        d, ds = delta("ventas")
        _metrica("Ventas del período", ars(actual.get("ventas")), ds, d, colores)
    with c2:
        d, ds = delta("inversion_medios")
        _metrica("Inversión en medios", ars(actual.get("inversion_medios")), ds, d, colores)
    with c3:
        d, ds = delta("presupuesto_total")
        _metrica("Presupuesto total MKT", ars(actual.get("presupuesto_total")), ds, d, colores)
    with c4:
        d, ds = delta("leads_validados")
        _metrica("Leads validados", num(actual.get("leads_validados")), ds, d, colores)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        d, ds = delta("otros_gastos_mkt")
        _metrica("Otros gastos MKT", ars(actual.get("otros_gastos_mkt")), ds, d, colores)
    with c2:
        d, ds = delta("ratio_presupuesto_ventas")
        _metrica("Ratio presupuesto/ventas", pct(actual.get("ratio_presupuesto_ventas")), ds, d, colores)
    with c3:
        inv   = actual.get("inversion_medios")
        leads = actual.get("leads_validados")
        cpl   = inv / leads if inv and leads and leads > 0 else None
        inv_p = anterior.get("inversion_medios")
        lea_p = anterior.get("leads_validados")
        cpl_p = inv_p / lea_p if inv_p and lea_p and lea_p > 0 else None
        d = variacion_pct(cpl, cpl_p)
        ds = f"{abs(d)*100:.1f}%" if d is not None else "—"
        _metrica("Costo por lead", ars(cpl), ds, d, colores)
    with c4:
        d, ds = delta("clientes_nuevos")
        _metrica("Clientes nuevos", num(actual.get("clientes_nuevos")), ds, d, colores)

    st.divider()
    st.markdown("##### Evolución histórica")

    df_plot = df_kpi.dropna(subset=["ventas"]).copy()
    df_plot["label"] = df_plot["fecha"].apply(periodo_label)

    tab1, tab2, tab3 = st.tabs(["Ventas", "Inversión vs Presupuesto", "Leads validados"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_plot["label"], y=df_plot["ventas"],
            mode="lines+markers", name="Ventas",
            line=dict(color=colores["primario"], width=2), marker=dict(size=5),
            hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>"
        ))
        fig.update_layout(
            height=320, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            xaxis=dict(gridcolor="#EEE", tickangle=-45), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_p = df_kpi.dropna(subset=["inversion_medios"]).copy()
        df_p["label"] = df_p["fecha"].apply(periodo_label)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_p["label"], y=df_p["inversion_medios"],
            name="Inversión medios", marker_color=colores["google"],
            hovertemplate="<b>%{x}</b><br>Inv. medios: $%{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Bar(x=df_p["label"], y=df_p["otros_gastos_mkt"],
            name="Otros gastos", marker_color=colores["secundario"],
            hovertemplate="<b>%{x}</b><br>Otros gastos: $%{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=df_p["label"], y=df_p["ventas"],
            name="Ventas", mode="lines",
            line=dict(color=colores["primario"], width=2, dash="dot"),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>"))
        fig.update_layout(
            barmode="stack", height=320, margin=dict(l=0,r=0,t=10,b=0),
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
        fig.add_trace(go.Bar(x=df_l["label"], y=df_l["leads_validados"],
            marker_color=colores["positivo"],
            hovertemplate="<b>%{x}</b><br>Leads: %{y:,.0f}<extra></extra>"))
        fig.update_layout(
            height=320, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#EEE"), xaxis=dict(tickangle=-45), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
