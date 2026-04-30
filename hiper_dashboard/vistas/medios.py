import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import ars, num, pct, periodo_label
from utils.config import COLORES

def render(datos: dict):
    df_ads  = datos.get("ads", pd.DataFrame())
    df_kpi  = datos.get("kpi", pd.DataFrame())
    df_ppto = datos.get("presupuesto", pd.DataFrame())

    if df_ads.empty:
        st.warning("Sin datos de ads.")
        return

    df_ads = df_ads.copy()
    df_ads["fecha"] = pd.to_datetime(df_ads["fecha"], errors="coerce")
    df_ads = df_ads.dropna(subset=["fecha"])
    df_ads["periodo"] = df_ads["fecha"].dt.to_period("M")
    df_ads["plataforma"] = df_ads["plataforma"].str.lower().str.strip()

    periodos = sorted(df_ads["periodo"].unique(), reverse=True)
    sel = st.selectbox("Período", [str(p) for p in periodos], index=0, key="medios_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    df_mes  = df_ads[df_ads["periodo"] == periodo_sel]
    df_ant  = df_ads[df_ads["periodo"] == (periodo_sel - 1)]

    st.divider()

    # KPIs por plataforma
    def kpis_plataforma(df, plat):
        d = df[df["plataforma"] == plat]
        return {
            "costo":       d["costo"].sum(),
            "impresiones": d["impresiones"].sum(),
            "clics":       d["clics"].sum(),
            "conversiones":d["conversiones"].sum() if "conversiones" in d.columns else 0,
        }

    g_mes  = kpis_plataforma(df_mes, "google")
    m_mes  = kpis_plataforma(df_mes, "meta")
    g_ant  = kpis_plataforma(df_ant, "google")
    m_ant  = kpis_plataforma(df_ant, "meta")

    inv_total = g_mes["costo"] + m_mes["costo"]

    # Leads del período para CPL
    df_lv = datos.get("leads", pd.DataFrame())
    leads_mes = 0
    if not df_lv.empty:
        df_lv = df_lv.copy()
        df_lv["fecha"] = pd.to_datetime(df_lv["fecha"], errors="coerce")
        leads_mes = df_lv[df_lv["fecha"].dt.to_period("M") == periodo_sel]["cantidad"].sum()

    cpl = inv_total / leads_mes if leads_mes > 0 else None

    # Métricas
    c1,c2,c3,c4 = st.columns(4)
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
            cc1, cc2 = st.columns([2,2])
            cc1.markdown(f"<small style='color:#666'>{label}</small>", unsafe_allow_html=True)
            cc2.markdown(f"**{val}**")

    with col_b:
        st.markdown("##### Meta Ads — detalle")
        ctr_m = m_mes["clics"] / m_mes["impresiones"] if m_mes["impresiones"] > 0 else 0
        cpc_m = m_mes["costo"] / m_mes["clics"] if m_mes["clics"] > 0 else 0
        rows = [
            ("Inversión", ars(m_mes["costo"])),
            ("Impresiones", num(m_mes["impresiones"])),
            ("Clics", num(m_mes["clics"])),
            ("CTR", f"{ctr_m*100:.2f}%"),
            ("CPC promedio", ars(cpc_m)),
            ("Resultados", num(m_mes["conversiones"])),
            ("Costo por resultado", ars(m_mes["costo"]/m_mes["conversiones"]) if m_mes["conversiones"] > 0 else "—"),
        ]
        for label, val in rows:
            cc1, cc2 = st.columns([2,2])
            cc1.markdown(f"<small style='color:#666'>{label}</small>", unsafe_allow_html=True)
            cc2.markdown(f"**{val}**")

    st.divider()
    st.markdown("##### Evolución de inversión por plataforma")

    df_monthly = df_ads.groupby(["periodo","plataforma"])["costo"].sum().reset_index()
    df_monthly["label"] = df_monthly["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))
    df_g = df_monthly[df_monthly["plataforma"]=="google"].sort_values("periodo")
    df_m = df_monthly[df_monthly["plataforma"]=="meta"].sort_values("periodo")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_g["label"], y=df_g["costo"],
        name="Google Ads", mode="lines+markers",
        line=dict(color=COLORES["google"], width=2),
        hovertemplate="<b>%{x}</b><br>Google: $%{y:,.0f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_m["label"], y=df_m["costo"],
        name="Meta Ads", mode="lines+markers",
        line=dict(color=COLORES["meta"], width=2),
        hovertemplate="<b>%{x}</b><br>Meta: $%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        height=300, margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Campañas del período
    st.markdown("##### Campañas del período")
    if not df_mes.empty:
        df_camp = df_mes.groupby(["plataforma","campaña"]).agg(
            costo=("costo","sum"),
            impresiones=("impresiones","sum"),
            clics=("clics","sum"),
            conversiones=("conversiones","sum"),
        ).reset_index().sort_values("costo", ascending=False)
        df_camp["ctr"] = (df_camp["clics"]/df_camp["impresiones"]).apply(lambda x: f"{x*100:.2f}%" if x > 0 else "—")
        df_camp["costo_fmt"] = df_camp["costo"].apply(ars)
        df_camp["impresiones"] = df_camp["impresiones"].apply(lambda x: num(x))
        df_camp["clics"] = df_camp["clics"].apply(lambda x: num(x))
        st.dataframe(
            df_camp[["plataforma","campaña","costo_fmt","impresiones","clics","ctr","conversiones"]].rename(columns={"costo_fmt":"costo"}),
            use_container_width=True, hide_index=True
        )
