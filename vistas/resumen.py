import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from etl.kpi import ultimo_mes, kpi_mes, mes_anterior, variacion_pct
from utils.formato import ars, pct, num, periodo_label
from utils.config import COLORES


def _safe_float(x):
    try:
        if x is None or x == "" or pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def _metrica(label, valor_fmt, delta_txt, delta_val):
    es_pos = delta_val is not None and delta_val >= 0
    color = COLORES["positivo"] if es_pos else COLORES["negativo"]
    icono = "▲" if es_pos else "▼"
    delta_html = (
        f'<span style="color:{color};font-size:13px">{icono} {delta_txt}</span>'
        if delta_txt and delta_txt != "—"
        else ""
    )

    st.markdown(
        f"""
        <div style="background:#F8F9FA;border-radius:10px;padding:16px 18px;border-left:4px solid {COLORES['secundario']}">
            <div style="font-size:12px;color:#666;margin-bottom:4px">{label}</div>
            <div style="font-size:24px;font-weight:600;color:{COLORES['secundario']}">{valor_fmt}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _clientes_nuevos_desde_ventas(df_v, periodo):
    if df_v is None or df_v.empty or "fecha" not in df_v.columns or "cliente" not in df_v.columns:
        return None

    periodo = pd.Period(periodo, freq="M")

    df = df_v.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["fecha"]).copy()

    if df.empty:
        return None

    df["periodo"] = df["fecha"].dt.to_period("M")
    df["cliente_norm"] = (
        df["cliente"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    clientes_mes = set(
        df.loc[df["periodo"] == periodo, "cliente_norm"]
        .dropna()
        .tolist()
    )

    clientes_anteriores = set(
        df.loc[df["periodo"] < periodo, "cliente_norm"]
        .dropna()
        .tolist()
    )

    if not clientes_mes:
        return 0

    nuevos = clientes_mes - clientes_anteriores
    return len(nuevos)

    df = df_v.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["fecha"]).copy()

    if df.empty:
        return None

    df["periodo"] = df["fecha"].dt.to_period("M")
    df["cliente_norm"] = (
        df["cliente"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    clientes_mes = set(
        df.loc[df["periodo"] == periodo, "cliente_norm"]
        .dropna()
        .tolist()
    )

    clientes_anteriores = set(
        df.loc[df["periodo"] < periodo, "cliente_norm"]
        .dropna()
        .tolist()
    )

    if not clientes_mes:
        return 0

    nuevos = clientes_mes - clientes_anteriores
    return len(nuevos)


def render(datos: dict):
    df_kpi = datos.get("kpi", pd.DataFrame())
    df_v = datos.get("ventas", pd.DataFrame())

    if df_kpi.empty:
        st.warning("Sin datos de KPI histórico.")
        return

    df_kpi = df_kpi.copy()
    if "fecha" in df_kpi.columns:
        df_kpi["fecha"] = pd.to_datetime(df_kpi["fecha"], errors="coerce", dayfirst=True)

    ult = ultimo_mes(df_kpi)
    if ult is None:
        st.warning("Sin datos disponibles.")
        return

    actual = kpi_mes(df_kpi, ult)
    anterior = mes_anterior(df_kpi, ult)

    # ===== KPIs base =====
    ventas = _safe_float(actual.get("ventas"))
    ventas_p = _safe_float(anterior.get("ventas"))

    inversion = _safe_float(actual.get("inversion_medios"))
    inversion_p = _safe_float(anterior.get("inversion_medios"))

    presupuesto_total = _safe_float(actual.get("presupuesto_total"))
    presupuesto_total_p = _safe_float(anterior.get("presupuesto_total"))

    leads = _safe_float(actual.get("leads_validados"))
    leads_p = _safe_float(anterior.get("leads_validados"))

    otros_gastos = _safe_float(actual.get("otros_gastos_mkt"))
    otros_gastos_p = _safe_float(anterior.get("otros_gastos_mkt"))

    # ===== KPIs derivados =====
    ratio_presupuesto_ventas = (
        presupuesto_total / ventas
        if presupuesto_total is not None and ventas not in (None, 0)
        else None
    )
    ratio_presupuesto_ventas_p = (
        presupuesto_total_p / ventas_p
        if presupuesto_total_p is not None and ventas_p not in (None, 0)
        else None
    )

    cpl = (
        inversion / leads
        if inversion is not None and leads not in (None, 0)
        else None
    )
    cpl_p = (
        inversion_p / leads_p
        if inversion_p is not None and leads_p not in (None, 0)
        else None
    )

    clientes_nuevos = _clientes_nuevos_desde_ventas(df_v, ult)
    clientes_nuevos_p = _clientes_nuevos_desde_ventas(df_v, ult - 1)

    # Header
    st.markdown(f"### Resumen ejecutivo — {periodo_label(ult)}")
    st.caption("Comparado con el mes anterior")
    st.divider()

    # ===== Fila 1 =====
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        dv = variacion_pct(ventas, ventas_p)
        _metrica(
            "Ventas del período",
            ars(ventas),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    with c2:
        dv = variacion_pct(inversion, inversion_p)
        _metrica(
            "Inversión en medios",
            ars(inversion),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    with c3:
        dv = variacion_pct(presupuesto_total, presupuesto_total_p)
        _metrica(
            "Presupuesto total MKT",
            ars(presupuesto_total),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    with c4:
        dv = variacion_pct(leads, leads_p)
        _metrica(
            "Leads validados",
            num(leads),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ===== Fila 2 =====
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        dv = variacion_pct(otros_gastos, otros_gastos_p)
        _metrica(
            "Otros gastos MKT",
            ars(otros_gastos),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    with c2:
        dv = variacion_pct(ratio_presupuesto_ventas, ratio_presupuesto_ventas_p)
        _metrica(
            "Ratio presupuesto/ventas",
            pct(ratio_presupuesto_ventas),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    with c3:
        dv = variacion_pct(cpl, cpl_p)
        _metrica(
            "Costo por lead",
            ars(cpl),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    with c4:
        dv = variacion_pct(clientes_nuevos, clientes_nuevos_p)
        _metrica(
            "Clientes nuevos",
            num(clientes_nuevos),
            f"{abs(dv)*100:.1f}%" if dv is not None else "—",
            dv,
        )

    st.divider()

    # ===== Gráfico evolución histórica =====
    st.markdown("##### Evolución histórica")

    df_plot = df_kpi.dropna(subset=["ventas"]).copy()
    df_plot["label"] = df_plot["fecha"].apply(periodo_label)

    tab1, tab2, tab3 = st.tabs(["Ventas", "Inversión vs Presupuesto", "Leads validados"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_plot["label"],
                y=df_plot["ventas"],
                mode="lines+markers",
                name="Ventas",
                line=dict(color=COLORES["primario"], width=2),
                marker=dict(size=5),
                hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            xaxis=dict(gridcolor="#EEE", tickangle=-45),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_p = df_kpi.dropna(subset=["inversion_medios", "presupuesto_total"]).copy()
        df_p["label"] = df_p["fecha"].apply(periodo_label)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df_p["label"],
                y=df_p["inversion_medios"],
                name="Inversión medios",
                marker_color=COLORES["google"],
                hovertemplate="<b>%{x}</b><br>Inv. medios: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                x=df_p["label"],
                y=df_p["otros_gastos_mkt"],
                name="Otros gastos",
                marker_color=COLORES["secundario"],
                hovertemplate="<b>%{x}</b><br>Otros gastos: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_p["label"],
                y=df_p["ventas"],
                name="Ventas",
                mode="lines",
                line=dict(color=COLORES["primario"], width=2, dash="dot"),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(
            barmode="stack",
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            yaxis2=dict(tickformat="$,.0f", overlaying="y", side="right", showgrid=False),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        df_l = df_kpi.dropna(subset=["leads_validados"]).copy()
        df_l["label"] = df_l["fecha"].apply(periodo_label)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df_l["label"],
                y=df_l["leads_validados"],
                marker_color=COLORES["positivo"],
                hovertemplate="<b>%{x}</b><br>Leads: %{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
