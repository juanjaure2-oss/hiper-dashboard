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
            "costo": _safe_float(d["costo"].sum()) if "costo" in d.columns else 0,
            "impresiones": _safe_float(d["impresiones"].sum()) if "impresiones" in d.columns else 0,
            "clics": _safe_float(d["clics"].sum()) if "clics" in d.columns else 0,
            "conversiones": _safe_float(d["conversiones"].sum()) if "conversiones" in d.columns else 0,
        }

    g_mes = kpis_plataforma(df_mes, "google")
    m_mes = kpis_plataforma(df_mes, "meta")
    g_ant = kpis_plataforma(df_ant, "google")
    m_ant = kpis_plataforma(df_ant, "meta")

    inv_total = _safe_float(g_mes["costo"]) + _safe_float(m_mes["costo"])

    # Leads del período para CPL
    df_lv = datos.get("leads", pd.DataFrame())
    leads_mes = 0.0
    if not df_lv.empty:
        df_lv = df_lv.copy()
        if "fecha" in df_lv.columns:
            df_lv["fecha"] = pd.to_datetime(df_lv["fecha"], errors="coerce")
            df_lv = df_lv.dropna(subset=["fecha"])
            if "cantidad" in df_lv.columns:
                leads_mes = _safe_float(
                    df_lv[df_lv["fecha"].dt.to_period("M") == periodo_sel]["cantidad"].sum()
                )

    cpl = inv_total / leads_mes if leads_mes > 0 else None

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inversión total medios", ars(inv_total))
    c2.metric("Google Ads", ars(g_mes["costo"]))
    c3.metric("Meta Ads", ars(m_mes["costo"]))
    c4.metric("Costo por lead", ars(cpl))

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("##### Google Ads — detalle")
        ctr_g = g_mes["clics"] / g_mes["impresiones"] if g_mes["impresiones"] > 0 else 0
        cpc_g = g_mes["costo"] / g_mes["clics"] if g_mes["clics"] > 0 else 0
        cpa_g = g_mes["costo"] / g_mes["conversiones"] if g_mes["conversiones"] > 0 else 0

        rows = [
            ("Inversión", ars(g_mes["costo"])),
            ("Impresiones", num(g_mes["impresiones"])),
            ("Clics", num(g_mes["clics"])),
            ("CTR", f"{ctr_g*100:.2f}%"),
            ("CPC promedio", ars(cpc_g)),
            ("Conversiones", num(g_mes["conversiones"])),
            ("CPA", ars(cpa_g) if g_mes["conversiones"] > 0 else "—"),
        ]

        for label, val in rows:
            cc1, cc2 = st.columns([2, 2])
            cc1.markdown(f"<small style='color:#666'>{label}</small>", unsafe_allow_html=True)
            cc2.markdown(f"**{val}**")

    with col_b:
        st.markdown("##### Meta Ads — detalle")
        ctr_m = m_mes["clics"] / m_mes["impresiones"] if m_mes["impresiones"] > 0 else 0
        cpc_m = m_mes["costo"] / m_mes["clics"] if m_mes["clics"] > 0 else 0
        cpr_m = m_mes["costo"] / m_mes["conversiones"] if m_mes["conversiones"] > 0 else 0

        rows = [
            ("Inversión", ars(m_mes["costo"])),
            ("Impresiones", num(m_mes["impresiones"])),
            ("Clics", num(m_mes["clics"])),
            ("CTR", f"{ctr_m*100:.2f}%"),
            ("CPC promedio", ars(cpc_m)),
            ("Resultados", num(m_mes["conversiones"])),
            ("Costo por resultado", ars(cpr_m) if m_mes["conversiones"] > 0 else "—"),
        ]

        for label, val in rows:
            cc1, cc2 = st.columns([2, 2])
            cc1.markdown(f"<small style='color:#666'>{label}</small>", unsafe_allow_html=True)
            cc2.markdown(f"**{val}**")

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
    fig.add_trace(
        go.Scatter(
            x=df_g["label"],
            y=df_g["costo"],
            name="Google Ads",
            mode="lines+markers",
            line=dict(color=COLORES["google"], width=2),
            hovertemplate="<b>%{x}</b><br>Google: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_m["label"],
            y=df_m["costo"],
            name="Meta Ads",
            mode="lines+markers",
            line=dict(color=COLORES["meta"], width=2),
            hovertemplate="<b>%{x}</b><br>Meta: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Campañas del período
    st.markdown("##### Campañas del período")
    if not df_mes.empty and "campaña" in df_mes.columns:
        df_camp = (
            df_mes.groupby(["plataforma", "campaña"])
            .agg(
                costo=("costo", "sum"),
                impresiones=("impresiones", "sum"),
                clics=("clics", "sum"),
                conversiones=("conversiones", "sum"),
            )
            .reset_index()
            .sort_values("costo", ascending=False)
        )

        df_camp["costo"] = pd.to_numeric(df_camp["costo"], errors="coerce").fillna(0)
        df_camp["impresiones"] = pd.to_numeric(df_camp["impresiones"], errors="coerce").fillna(0)
        df_camp["clics"] = pd.to_numeric(df_camp["clics"], errors="coerce").fillna(0)
        df_camp["conversiones"] = pd.to_numeric(df_camp["conversiones"], errors="coerce").fillna(0)

        df_camp["ctr"] = (
            df_camp["clics"] / df_camp["impresiones"].replace(0, pd.NA)
        ).apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) and x > 0 else "—")

        df_camp["costo_fmt"] = df_camp["costo"].apply(ars)
        df_camp["impresiones_fmt"] = df_camp["impresiones"].apply(num)
        df_camp["clics_fmt"] = df_camp["clics"].apply(num)
        df_camp["conversiones_fmt"] = df_camp["conversiones"].apply(num)

        st.dataframe(
            df_camp[
                ["plataforma", "campaña", "costo_fmt", "impresiones_fmt", "clics_fmt", "ctr", "conversiones_fmt"]
            ].rename(
                columns={
                    "costo_fmt": "costo",
                    "impresiones_fmt": "impresiones",
                    "clics_fmt": "clics",
                    "conversiones_fmt": "conversiones",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Sin campañas para el período seleccionado.")
