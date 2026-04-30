import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import ars, num, periodo_label

def render(datos: dict, colores: dict):
    df_ads = datos.get("ads", pd.DataFrame())
    if df_ads.empty:
        st.warning("Sin datos de ads.")
        return

    df_ads = df_ads.copy()
    df_ads["fecha"] = pd.to_datetime(df_ads["fecha"], errors="coerce")
    df_ads = df_ads.dropna(subset=["fecha"])
    df_ads["periodo"]    = df_ads["fecha"].dt.to_period("M")
    df_ads["plataforma"] = df_ads["plataforma"].str.lower().str.strip()

    periodos = sorted(df_ads["periodo"].unique(), reverse=True)
    sel = st.selectbox("Período", [str(p) for p in periodos], index=0, key="medios_periodo")
    periodo_sel = pd.Period(sel, freq="M")
    st.divider()

    df_mes = df_ads[df_ads["periodo"] == periodo_sel]
    df_ant = df_ads[df_ads["periodo"] == (periodo_sel - 1)]

    def kpis(df, plat):
        d = df[df["plataforma"] == plat]
        return {
            "costo":        d["costo"].sum()        if not d.empty else 0,
            "impresiones":  d["impresiones"].sum()  if not d.empty else 0,
            "clics":        d["clics"].sum()         if not d.empty else 0,
            "conversiones": d["conversiones"].sum()  if "conversiones" in d.columns and not d.empty else 0,
        }

    g = kpis(df_mes, "google")
    m = kpis(df_mes, "meta")
    inv_total = g["costo"] + m["costo"]

    # CPL
    df_lv = datos.get("leads", pd.DataFrame())
    leads_mes = 0
    if not df_lv.empty:
        df_lv = df_lv.copy()
        df_lv["fecha"] = pd.to_datetime(df_lv["fecha"], errors="coerce")
        leads_mes = int(df_lv[df_lv["fecha"].dt.to_period("M") == periodo_sel]["cantidad"].sum())
    cpl = inv_total / leads_mes if leads_mes > 0 else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inversión total medios", ars(inv_total))
    c2.metric("Google Ads",             ars(g["costo"]))
    c3.metric("Meta Ads",               ars(m["costo"]))
    c4.metric("Costo por lead",         ars(cpl))

    st.divider()
    col_a, col_b = st.columns(2)

    def detalle_plataforma(titulo, d, nombre):
        st.markdown(f"##### {titulo}")
        ctr = d["clics"] / d["impresiones"] if d["impresiones"] > 0 else 0
        cpc = d["costo"] / d["clics"]       if d["clics"]       > 0 else 0
        cpa = d["costo"] / d["conversiones"]if d["conversiones"]> 0 else 0
        filas = [
            ("Inversión",     ars(d["costo"])),
            ("Impresiones",   num(d["impresiones"])),
            ("Clics",         num(d["clics"])),
            ("CTR",           f"{ctr*100:.2f}%"),
            ("CPC promedio",  ars(cpc)),
            ("Conversiones",  num(d["conversiones"])),
            ("CPA",           ars(cpa) if d["conversiones"] > 0 else "—"),
        ]
        for lbl, val in filas:
            c1, c2 = st.columns(2)
            c1.markdown(f"<small style='color:#666'>{lbl}</small>", unsafe_allow_html=True)
            c2.markdown(f"**{val}**")

    with col_a:
        detalle_plataforma("Google Ads — detalle", g, "google")
    with col_b:
        detalle_plataforma("Meta Ads — detalle",   m, "meta")

    st.divider()
    st.markdown("##### Evolución de inversión por plataforma")

    df_monthly = (df_ads.groupby(["periodo","plataforma"])["costo"]
                  .sum().reset_index())
    df_monthly["label"] = df_monthly["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))

    fig = go.Figure()
    for plat, color in [("google", colores["google"]), ("meta", colores["meta"])]:
        d = df_monthly[df_monthly["plataforma"] == plat].sort_values("periodo")
        if d.empty: continue
        fig.add_trace(go.Scatter(
            x=d["label"], y=d["costo"],
            name=plat.capitalize(), mode="lines+markers",
            line=dict(color=color, width=2),
            hovertemplate=f"<b>%{{x}}</b><br>{plat.capitalize()}: $%{{y:,.0f}}<extra></extra>"
        ))
    fig.update_layout(
        height=300, margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Campañas del período")
    if not df_mes.empty:
        df_camp = (df_mes.groupby(["plataforma","campaña"])
                   .agg(costo=("costo","sum"), impresiones=("impresiones","sum"),
                        clics=("clics","sum"), conversiones=("conversiones","sum"))
                   .reset_index().sort_values("costo", ascending=False))
        df_camp["ctr"]   = (df_camp["clics"]/df_camp["impresiones"]).apply(
            lambda x: f"{x*100:.2f}%" if x > 0 else "—")
        df_camp["costo"] = df_camp["costo"].apply(ars)
        df_camp["impresiones"] = df_camp["impresiones"].apply(num)
        df_camp["clics"]       = df_camp["clics"].apply(num)
        st.dataframe(
            df_camp[["plataforma","campaña","costo","impresiones","clics","ctr","conversiones"]],
            use_container_width=True, hide_index=True
        )
