import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import num, periodo_label
from utils.config import COLORES

CANAL_COLORES = {
    "facebook": "#1877F2",
    "instagram": "#E1306C",
    "linkedin": "#0A66C2",
}


def _to_num(series):
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0)

    s = (
        series.astype(str)
        .str.strip()
        .replace({"": None, "nan": None, "None": None, "—": None})
    )

    mask_comma = s.str.contains(",", na=False)

    s_arg = (
        s.where(mask_comma)
        .str.replace("$", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    s_std = (
        s.where(~mask_comma)
        .str.replace("$", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    out = pd.Series(index=series.index, dtype="float64")
    out.loc[mask_comma] = pd.to_numeric(s_arg.loc[mask_comma], errors="coerce")
    out.loc[~mask_comma] = pd.to_numeric(s_std.loc[~mask_comma], errors="coerce")
    return out.fillna(0)


def render(datos: dict):
    df_r = datos.get("redes", pd.DataFrame())
    if df_r.empty:
        st.warning("Sin datos de redes.")
        return

    df_r = df_r.copy()

    for col in [
        "fecha",
        "canal",
        "seguidores_totales",
        "adquiridos",
        "impresiones",
        "interacciones",
        "cantidad_contenido",
    ]:
        if col not in df_r.columns:
            df_r[col] = 0 if col not in ["fecha", "canal"] else None

    df_r["fecha"] = pd.to_datetime(df_r["fecha"], errors="coerce", dayfirst=True)
    df_r = df_r.dropna(subset=["fecha"]).copy()

    if df_r.empty:
        st.warning("Sin fechas válidas en redes.")
        return

    df_r["canal"] = (
        df_r["canal"]
        .astype(str)
        .str.lower()
        .str.strip()
        .replace({
            "ig": "instagram",
            "insta": "instagram",
            "fb": "facebook",
            "linkedin ads": "linkedin",
        })
    )

    for col in ["seguidores_totales", "adquiridos", "impresiones", "interacciones", "cantidad_contenido"]:
        df_r[col] = _to_num(df_r[col])

    df_r["periodo"] = df_r["fecha"].dt.to_period("M")

    periodos = sorted(df_r["periodo"].dropna().unique(), reverse=True)
    if not periodos:
        st.warning("Sin períodos válidos en redes.")
        return

    sel = st.selectbox("Período", [str(p) for p in periodos], index=0, key="redes_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    df_agg = (
        df_r.groupby(["periodo", "canal"], as_index=False)
        .agg(
            seguidores_totales=("seguidores_totales", "max"),
            adquiridos=("adquiridos", "sum"),
            impresiones=("impresiones", "sum"),
            interacciones=("interacciones", "sum"),
            cantidad_contenido=("cantidad_contenido", "sum"),
        )
        .sort_values(["periodo", "canal"])
    )

    df_mes = df_agg[df_agg["periodo"] == periodo_sel].copy()

    st.divider()

    canales = ["facebook", "instagram", "linkedin"]
    cols = st.columns(len(canales))

    for i, canal in enumerate(canales):
        d = df_mes[df_mes["canal"] == canal]

        with cols[i]:
            nombre = canal.capitalize()
            color = CANAL_COLORES.get(canal, COLORES["secundario"])

            if d.empty:
                st.markdown(
                    f"""
                    <div style="background:#F8F9FA;border-radius:10px;padding:14px;border-top:4px solid {color}">
                        <div style="font-weight:700;color:{color};margin-bottom:10px">{nombre}</div>
                        <div style="color:#666;font-size:13px">Sin datos</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                row = d.iloc[0]

                st.markdown(
                    f"""
                    <div style="background:#F8F9FA;border-radius:10px;padding:14px;border-top:4px solid {color}">
                        <div style="font-weight:700;color:{color};margin-bottom:12px">{nombre}</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 18px">
                            <div>
                                <div style="font-size:12px;color:#666">Seguidores</div>
                                <div style="font-size:22px;font-weight:700;color:#1D1D1B">{num(row["seguidores_totales"])}</div>
                            </div>
                            <div>
                                <div style="font-size:12px;color:#666">Adquiridos</div>
                                <div style="font-size:22px;font-weight:700;color:#1D1D1B">+{num(row["adquiridos"])}</div>
                            </div>
                            <div>
                                <div style="font-size:12px;color:#666">Impresiones</div>
                                <div style="font-size:22px;font-weight:700;color:#1D1D1B">{num(row["impresiones"])}</div>
                            </div>
                            <div>
                                <div style="font-size:12px;color:#666">Interacciones</div>
                                <div style="font-size:22px;font-weight:700;color:#1D1D1B">{num(row["interacciones"])}</div>
                            </div>
                            <div>
                                <div style="font-size:12px;color:#666">Contenidos</div>
                                <div style="font-size:22px;font-weight:700;color:#1D1D1B">{num(row["cantidad_contenido"])}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Seguidores", "Impresiones", "Interacciones"])

    def grafico_evolucion(metrica):
        fig = go.Figure()
        for canal in canales:
            df_canal = df_agg[df_agg["canal"] == canal].sort_values("periodo").copy()
            if df_canal.empty or metrica not in df_canal.columns:
                continue

            df_canal["label"] = df_canal["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))

            fig.add_trace(
                go.Scatter(
                    x=df_canal["label"],
                    y=df_canal[metrica],
                    name=canal.capitalize(),
                    mode="lines+markers",
                    line=dict(color=CANAL_COLORES.get(canal, "#999"), width=2),
                    marker=dict(size=6),
                    hovertemplate=f"<b>%{{x}}</b><br>{canal.capitalize()}: %{{y:,.0f}}<extra></extra>",
                )
            )

        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        return fig

    with tab1:
        st.plotly_chart(grafico_evolucion("seguidores_totales"), use_container_width=True)
    with tab2:
        st.plotly_chart(grafico_evolucion("impresiones"), use_container_width=True)
    with tab3:
        st.plotly_chart(grafico_evolucion("interacciones"), use_container_width=True)

    st.divider()
    st.markdown("##### Contenido publicado por mes")

    df_cont = (
        df_agg.groupby(["periodo", "canal"], as_index=False)["cantidad_contenido"]
        .sum()
        .sort_values(["periodo", "canal"])
    )
    df_cont["label"] = df_cont["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))

    fig_cont = go.Figure()
    for canal in canales:
        d = df_cont[df_cont["canal"] == canal]
        if d.empty:
            continue

        fig_cont.add_trace(
            go.Bar(
                x=d["label"],
                y=d["cantidad_contenido"],
                name=canal.capitalize(),
                marker_color=CANAL_COLORES.get(canal, "#999"),
                hovertemplate=f"<b>%{{x}}</b><br>{canal.capitalize()}: %{{y}} piezas<extra></extra>",
            )
        )

    fig_cont.update_layout(
        barmode="group",
        height=260,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#EEE"),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_cont, use_container_width=True)
