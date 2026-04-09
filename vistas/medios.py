import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import ars, num, pct, periodo_label
from utils.config import COLORES


def _safe_float(x):
    try:
        if x is None or x == "" or pd.isna(x):
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def render(datos: dict):
    df_ads = datos.get("ads", pd.DataFrame())
    df_kpi = datos.get("kpi", pd.DataFrame())
    df_ppto = datos.get("presupuesto", pd.DataFrame())

    if df_ads.empty:
        st.warning("Sin datos de ads.")
        return

    df_ads = df_ads.copy()
    df_ads["fecha"] = pd.to_datetime(df_ads["fecha"], errors="coerce")
    df_ads = df_ads.dropna(subset=["fecha"])
    df_ads["periodo"] = df_ads["fecha"].dt.to_period("M")

    if "plataforma" in df_ads.columns:
        df_ads["plataforma"] = df_ads["plataforma"].astype(str).str.lower().str.strip()
    else:
        df_ads["plataforma"] = ""

    for col in ["costo", "impresiones", "clics", "conversiones"]:
        if col not in df_ads.columns:
            df_ads[col] = 0

    periodos = sorted(df_ads["periodo"].unique(), reverse=True)
    if not periodos:
        st.warning("Sin períodos válidos en ads.")
        return

    sel = st.selectbox("Período", [str(p) for p in periodos], index=0, key="medios_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    df_mes = df_ads[df_ads["periodo"] == periodo_sel]
    df_ant = df_ads[df_ads["periodo"] == (periodo_sel - 1)]

    st.divider()

    def kpis_plataforma(df, plat):
        d = df[df["plataforma"] == plat]
        return {
            "costo": _safe_float(d["costo"].sum()),
            "impresiones": _safe_float(d["impresiones"].sum()),
            "clics": _safe_float(d["clics"].sum()),
            "conversiones": _safe_float(d["conversiones"].sum()),
        }

    g_mes = kpis_plataforma(df_mes, "google")
    m_mes = kpis_plataforma(df_mes, "meta")

    inv_total = g_mes["costo"] + m_mes["costo"]

    # Leads para CPL
    df_lv = datos.get("leads", pd.DataFrame())
    leads_mes = 0.0
    if not df_lv.empty and "fecha" in df_lv.columns and "cantidad" in df_lv.columns:
        df_lv = df_lv.copy()
        df_lv["fecha"] = pd.to_datetime(df_lv["fecha"], errors="coerce")
        df_lv = df_lv.dropna(subset=["fecha"])
        leads_mes = _safe_float(
            df_lv[df_lv["fecha"].dt.to_period("M") == periodo_sel]["cantidad"].sum()
        )

    cpl = inv_total / leads_mes if leads_mes > 0 else None

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inversión total medios", ars(inv_total))
    c2.metric("Google Ads", ars(g_mes["costo"]))
    c3.metric("Meta Ads", ars(m_mes["costo"]))
    c4.metric("Costo por lead", ars(cpl))

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("##### Google Ads — detalle")
        ctr = g_mes["clics"] / g_mes["impresiones"] if g_mes["impresiones"] else 0
        cpc = g_mes["costo"] / g_mes["clics"] if g_mes["clics"] else 0

        for k, v in [
            ("Inversión", ars(g_mes["costo"])),
            ("Impresiones", num(g_mes["impresiones"])),
            ("Clics", num(g_mes["clics"])),
            ("CTR", f"{ctr*100:.2f}%"),
            ("CPC", ars(cpc)),
        ]:
            a, b = st.columns([2, 2])
            a.markdown(f"<small>{k}</small>", unsafe_allow_html=True)
            b.markdown(f"**{v}**")

    with col_b:
        st.markdown("##### Meta Ads — detalle")
        ctr = m_mes["clics"] / m_mes["impresiones"] if m_mes["impresiones"] else 0
        cpc = m_mes["costo"] / m_mes["clics"] if m_mes["clics"] else 0

        for k, v in [
            ("Inversión", ars(m_mes["costo"])),
            ("Impresiones", num(m_mes["impresiones"])),
            ("Clics", num(m_mes["clics"])),
            ("CTR", f"{ctr*100:.2f}%"),
            ("CPC", ars(cpc)),
        ]:
            a, b = st.columns([2, 2])
            a.markdown(f"<small>{k}</small>", unsafe_allow_html=True)
            b.markdown(f"**{v}**")

    st.divider()
    st.markdown("##### Evolución de inversión por plataforma")

    df_monthly = (
        df_ads.groupby(["periodo", "plataforma"])["costo"]
        .sum()
        .reset_index()
    )

    df_monthly["label"] = df_monthly["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))

    df_g = df_monthly[df_monthly["plataforma"] == "google"].sort_values("periodo")
    df_m = df_monthly[df_monthly["plataforma"] == "meta"].sort_values("periodo")

    fig = go.Figure()

    # Google Ads
    fig.add_trace(
        go.Scatter(
            x=df_g["label"],
            y=df_g["costo"],
            name="Google Ads",
            mode="lines+markers",
            line=dict(color="#34A853", width=3),
            marker=dict(size=7, symbol="circle"),
        )
    )

    # Meta Ads
    fig.add_trace(
        go.Scatter(
            x=df_m["label"],
            y=df_m["costo"],
            name="Meta Ads",
            mode="lines+markers",
            line=dict(color="#1877F2", width=3, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
        )
    )

    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Campañas
    st.markdown("##### Campañas del período")

    if not df_mes.empty and "campaña" in df_mes.columns:
        df_camp = (
            df_mes.groupby(["plataforma", "campaña"])
            .agg(costo=("costo", "sum"), clics=("clics", "sum"))
            .reset_index()
            .sort_values("costo", ascending=False)
        )

        df_camp["costo"] = df_camp["costo"].apply(ars)
        df_camp["clics"] = df_camp["clics"].apply(num)

        st.dataframe(df_camp, use_container_width=True, hide_index=True)
    else:
        st.info("Sin campañas para el período seleccionado.")
