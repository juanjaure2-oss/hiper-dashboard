import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import num, periodo_label, variacion
from utils.config import COLORES


ORDEN_EMBUDO = [
    "cliente activo",
    "en oportunidad (cotizando)",
    "lead templado (scoring - no usar factibilidad))",
    "lead caliente (scoring - no usar factibilidad))",
    "lead frío (dato sin calificación)",
    "lead sin contacto (se llamó 5 días diferentes)",
    "lead perdido (automático)",
    "cliente perdido (especificar motivo)",
    "otro descartado (no califica)",
]

LABELS_CORTOS = {
    "cliente activo": "Cliente activo",
    "en oportunidad (cotizando)": "En oportunidad",
    "lead templado (scoring - no usar factibilidad))": "Lead templado",
    "lead caliente (scoring - no usar factibilidad))": "Lead caliente",
    "lead frío (dato sin calificación)": "Lead frío",
    "lead sin contacto (se llamó 5 días diferentes)": "Sin contacto",
    "lead perdido (automático)": "Lead perdido",
    "cliente perdido (especificar motivo)": "Cliente perdido",
    "otro descartado (no califica)": "Descartado",
}


def _metrica_html(label, valor, delta_txt=None, delta_val=None):
    delta_html = ""
    if delta_txt is not None and delta_val is not None:
        es_pos = delta_val >= 0
        color = COLORES["positivo"] if es_pos else COLORES["negativo"]
        icono = "▲" if es_pos else "▼"
        delta_html = f'<div style="font-size:13px;color:{color};margin-top:6px">{icono} {delta_txt}</div>'

    st.markdown(
        f"""
        <div style="background:#F8F9FA;border-radius:10px;padding:16px 18px;border-left:4px solid {COLORES['secundario']}">
            <div style="font-size:12px;color:#666;margin-bottom:4px">{label}</div>
            <div style="font-size:24px;font-weight:600;color:{COLORES['secundario']}">{valor}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _normalizar_texto(s, default="Sin dato"):
    if s is None:
        return pd.Series(dtype="object")
    out = s.astype(str).str.strip()
    out = out.replace(
        {
            "": default,
            "nan": default,
            "None": default,
            "0": "Desconocido",
            "-": default,
        }
    )
    return out.fillna(default)


def _estado_counts(df):
    if df.empty or "estado" not in df.columns:
        return pd.DataFrame(columns=["estado", "cantidad", "label", "orden"])

    estados = _normalizar_texto(df["estado"], default="Sin estado")
    vc = estados.value_counts().reset_index()
    vc.columns = ["estado", "cantidad"]
    vc["label"] = vc["estado"].map(LABELS_CORTOS).fillna(vc["estado"])
    vc["orden"] = vc["estado"].apply(lambda x: ORDEN_EMBUDO.index(x) if x in ORDEN_EMBUDO else 999)
    return vc.sort_values(["orden", "cantidad"], ascending=[True, False]).reset_index(drop=True)


def render(datos: dict):
    df_crm = datos.get("crm", pd.DataFrame())
    df_lv = datos.get("leads", pd.DataFrame())

    if df_crm.empty:
        st.warning("Sin datos de CRM.")
        return

    df_crm = df_crm.copy()

    # Asegurar columnas
    for col in ["estado", "tipo", "origen_contacto", "fecha_creado", "ultimo_contacto", "provincia"]:
        if col not in df_crm.columns:
            df_crm[col] = None

    df_crm["fecha_creado"] = pd.to_datetime(df_crm["fecha_creado"], errors="coerce", dayfirst=True)
    df_crm["ultimo_contacto"] = pd.to_datetime(df_crm["ultimo_contacto"], errors="coerce", dayfirst=True)

    df_crm["estado"] = _normalizar_texto(df_crm["estado"], default="Sin estado")
    df_crm["tipo"] = _normalizar_texto(df_crm["tipo"], default="Sin tipo")
    df_crm["provincia"] = _normalizar_texto(df_crm["provincia"], default="Sin dato")
    df_crm["origen_contacto"] = _normalizar_texto(df_crm["origen_contacto"], default="Desconocido").replace(
        {"0": "Desconocido"}
    )

    df_valid = df_crm.dropna(subset=["fecha_creado"]).copy()
    if df_valid.empty:
        st.warning("El CRM no tiene fechas de creación válidas.")
        return

    df_valid["periodo"] = df_valid["fecha_creado"].dt.to_period("M")

    periodos = sorted(df_valid["periodo"].dropna().unique(), reverse=True)
    if not periodos:
        st.warning("No hay períodos válidos en CRM.")
        return

    labels_periodos = [str(p) for p in periodos]

    st.markdown("##### CRM y embudo")

    col_sel1, col_sel2 = st.columns([3, 2])
    with col_sel1:
        sel = st.selectbox("Período", labels_periodos, index=0, key="crm_periodo")

    periodo_sel = pd.Period(sel, freq="M")
    periodo_ant = periodo_sel - 1

    df_mes = df_valid[df_valid["periodo"] == periodo_sel].copy()
    df_mes_ant = df_valid[df_valid["periodo"] == periodo_ant].copy()

    # KPIs mensuales
    total_mes = len(df_mes)
    total_ant = len(df_mes_ant)

    oportunidades_mes = len(df_mes[df_mes["estado"].str.contains("oportunidad", case=False, na=False)])
    oportunidades_ant = len(df_mes_ant[df_mes_ant["estado"].str.contains("oportunidad", case=False, na=False)])

    activos_mes = len(df_mes[df_mes["estado"].str.contains("cliente activo", case=False, na=False)])
    activos_ant = len(df_mes_ant[df_mes_ant["estado"].str.contains("cliente activo", case=False, na=False)])

    descartados_mes = len(df_mes[df_mes["estado"].str.contains("descartado|perdido", case=False, na=False)])
    descartados_ant = len(df_mes_ant[df_mes_ant["estado"].str.contains("descartado|perdido", case=False, na=False)])

    tasa_oportunidad_mes = (oportunidades_mes / total_mes) if total_mes > 0 else None
    tasa_oportunidad_ant = (oportunidades_ant / total_ant) if total_ant > 0 else None

    d1, t1 = variacion(total_mes, total_ant)
    d2, t2 = variacion(oportunidades_mes, oportunidades_ant)
    d3, t3 = variacion(activos_mes, activos_ant)
    d4, t4 = variacion(descartados_mes, descartados_ant)
    d5, t5 = variacion(tasa_oportunidad_mes, tasa_oportunidad_ant)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        _metrica_html("Contactos creados", num(total_mes), None if t1 == "—" else t1, d1)
    with c2:
        _metrica_html("En oportunidad", num(oportunidades_mes), None if t2 == "—" else t2, d2)
    with c3:
        _metrica_html("Clientes activos", num(activos_mes), None if t3 == "—" else t3, d3)
    with c4:
        _metrica_html("Descartados / perdidos", num(descartados_mes), None if t4 == "—" else t4, d4)
    with c5:
        _metrica_html(
            "Tasa de oportunidad",
            f"{tasa_oportunidad_mes * 100:.1f}%" if tasa_oportunidad_mes is not None else "—",
            None if t5 == "—" else t5,
            d5,
        )

    st.divider()

    tab1, tab2 = st.tabs(["Estado actual", f"Altas del período ({sel})"])

    with tab1:
        st.markdown("##### Embudo comercial — estado actual")
        estados = _estado_counts(df_crm)

        col_a, col_b = st.columns([3, 2])

        with col_a:
            fig = go.Figure(
                go.Bar(
                    x=estados["cantidad"],
                    y=estados["label"],
                    orientation="h",
                    marker_color=COLORES["secundario"],
                    text=estados["cantidad"],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x:,d} contactos<extra></extra>",
                )
            )
            fig.update_layout(
                height=340,
                margin=dict(l=0, r=50, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="#EEE"),
                yaxis=dict(autorange="reversed"),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            total = len(df_crm)
            activos = len(df_crm[df_crm["estado"].str.contains("cliente activo", case=False, na=False)])
            oportunidad = len(df_crm[df_crm["estado"].str.contains("oportunidad", case=False, na=False)])
            descartados = len(df_crm[df_crm["estado"].str.contains("descartado|perdido", case=False, na=False)])

            st.markdown("**Resumen CRM actual**")
            metricas = [
                ("Total contactos", num(total)),
                ("Clientes activos", num(activos)),
                ("En oportunidad", num(oportunidad)),
                ("Descartados/perdidos", num(descartados)),
                ("Tasa activación", f"{(activos / total) * 100:.1f}%" if total > 0 else "—"),
            ]
            for label, val in metricas:
                a, b = st.columns(2)
                a.markdown(f"<small style='color:#666'>{label}</small>", unsafe_allow_html=True)
                b.markdown(f"**{val}**")

    with tab2:
        st.markdown(f"##### Altas CRM — {periodo_label(periodo_sel.to_timestamp())}")
        estados_mes = _estado_counts(df_mes)

        col_a, col_b = st.columns([3, 2])

        with col_a:
            fig = go.Figure(
                go.Bar(
                    x=estados_mes["cantidad"],
                    y=estados_mes["label"],
                    orientation="h",
                    marker_color=COLORES["primario"],
                    text=estados_mes["cantidad"],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x:,d} contactos<extra></extra>",
                )
            )
            fig.update_layout(
                height=340,
                margin=dict(l=0, r=50, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="#EEE"),
                yaxis=dict(autorange="reversed"),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("**Resumen del período**")
            metricas = [
                ("Contactos creados", num(total_mes)),
                ("En oportunidad", num(oportunidades_mes)),
                ("Clientes activos", num(activos_mes)),
                ("Descartados/perdidos", num(descartados_mes)),
                ("Tasa de oportunidad", f"{tasa_oportunidad_mes * 100:.1f}%" if tasa_oportunidad_mes is not None else "—"),
            ]
            for label, val in metricas:
                a, b = st.columns(2)
                a.markdown(f"<small style='color:#666'>{label}</small>", unsafe_allow_html=True)
                b.markdown(f"**{val}**")

    st.divider()

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown(f"##### Distribución por provincia — {sel}")
        prov = (
            df_mes["provincia"]
            .fillna("Sin dato")
            .value_counts()
            .head(12)
            .reset_index()
        )
        prov.columns = ["provincia", "cantidad"]

        fig_p = go.Figure(
            go.Bar(
                x=prov["cantidad"],
                y=prov["provincia"],
                orientation="h",
                marker_color=COLORES["primario"],
                hovertemplate="<b>%{y}</b><br>%{x:,d}<extra></extra>",
            )
        )
        fig_p.update_layout(
            height=350,
            margin=dict(l=0, r=30, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#EEE"),
            yaxis=dict(autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(fig_p, use_container_width=True)

    with col_d:
        st.markdown(f"##### Origen de contactos — {sel}")
        orig = (
            df_mes["origen_contacto"]
            .fillna("Desconocido")
            .replace({"0": "Desconocido"})
            .value_counts()
            .head(10)
            .reset_index()
        )
        orig.columns = ["origen", "cantidad"]

        fig_o = go.Figure(
            go.Pie(
                labels=orig["origen"],
                values=orig["cantidad"],
                hole=0.4,
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>%{value:,d}<extra></extra>",
            )
        )
        fig_o.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_o, use_container_width=True)

    st.divider()
    st.markdown("##### Leads validados")

    if not df_lv.empty and "fecha" in df_lv.columns and "cantidad" in df_lv.columns:
        df_lv = df_lv.copy()
        df_lv["fecha"] = pd.to_datetime(df_lv["fecha"], errors="coerce", dayfirst=True)
        df_lv = df_lv.dropna(subset=["fecha"]).copy()
        df_lv["periodo"] = df_lv["fecha"].dt.to_period("M")

        lv_mes = df_lv.loc[df_lv["periodo"] == periodo_sel, "cantidad"].sum()
        lv_ant = df_lv.loc[df_lv["periodo"] == periodo_ant, "cantidad"].sum()

        dv_lv, txt_lv = variacion(lv_mes, lv_ant)

        a1, a2 = st.columns([1, 3])
        with a1:
            _metrica_html("Leads validados del período", num(lv_mes), None if txt_lv == "—" else txt_lv, dv_lv)

        with a2:
            monthly = (
                df_lv.groupby("periodo", as_index=False)["cantidad"]
                .sum()
                .sort_values("periodo")
            )
            monthly["label"] = monthly["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))

            fig_lv = go.Figure(
                go.Bar(
                    x=monthly["label"],
                    y=monthly["cantidad"],
                    marker_color=COLORES["positivo"],
                    hovertemplate="<b>%{x}</b><br>Leads: %{y:,d}<extra></extra>",
                )
            )
            fig_lv.update_layout(
                height=280,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#EEE"),
                xaxis=dict(tickangle=-45),
                showlegend=False,
            )
            st.plotly_chart(fig_lv, use_container_width=True)
    else:
        st.info("Sin datos de leads validados.")
