import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.formato import num, periodo_label
from utils.config import COLORES

def render(datos: dict):
    df_crm = datos.get("crm", pd.DataFrame())
    df_lv  = datos.get("leads", pd.DataFrame())
    df_kpi = datos.get("kpi", pd.DataFrame())

    if df_crm.empty:
        st.warning("Sin datos de CRM.")
        return

    df_crm = df_crm.copy()
    df_crm["fecha_creado"] = pd.to_datetime(df_crm["fecha_creado"], errors="coerce")

    st.markdown("##### Embudo comercial — estado actual")

    # Estado counts
    estados = df_crm["estado"].value_counts().reset_index()
    estados.columns = ["estado","cantidad"]

    orden_embudo = [
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
    # Short labels
    labels_cortos = {
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
    estados["label"] = estados["estado"].map(labels_cortos).fillna(estados["estado"])

    col_a, col_b = st.columns([3,2])

    with col_a:
        colores_embudo = [
            COLORES["positivo"], "#2980B9", "#8E44AD", "#E74C3C",
            COLORES["neutro"],"#BDC3C7","#E74C3C","#C0392B","#95A5A6"
        ]
        fig = go.Figure(go.Bar(
            x=estados["cantidad"],
            y=estados["label"],
            orientation="h",
            marker_color=COLORES["secundario"],
            text=estados["cantidad"],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:,d} contactos<extra></extra>"
        ))
        fig.update_layout(
            height=320, margin=dict(l=0,r=50,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#EEE"),
            yaxis=dict(autorange="reversed"),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        total = len(df_crm)
        activos = len(df_crm[df_crm["estado"] == "cliente activo"])
        oportunidad = len(df_crm[df_crm["estado"] == "en oportunidad (cotizando)"])
        descartados = len(df_crm[df_crm["estado"].str.contains("descartado|perdido", case=False, na=False)])

        st.markdown("**Resumen CRM**")
        metricas = [
            ("Total contactos", num(total)),
            ("Clientes activos", num(activos)),
            ("En oportunidad", num(oportunidad)),
            ("Descartados/perdidos", num(descartados)),
            ("Tasa activación", f"{activos/total*100:.1f}%" if total > 0 else "—"),
        ]
        for label, val in metricas:
            c1, c2 = st.columns(2)
            c1.markdown(f"<small style='color:#666'>{label}</small>", unsafe_allow_html=True)
            c2.markdown(f"**{val}**")

    st.divider()

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("##### Distribución por provincia")
        prov = df_crm[df_crm["provincia"].notna() & (df_crm["provincia"] != "")]["provincia"].value_counts().head(12).reset_index()
        prov.columns = ["provincia","cantidad"]
        fig_p = go.Figure(go.Bar(
            x=prov["cantidad"], y=prov["provincia"],
            orientation="h",
            marker_color=COLORES["primario"],
            hovertemplate="<b>%{y}</b><br>%{x:,d}<extra></extra>"
        ))
        fig_p.update_layout(
            height=350, margin=dict(l=0,r=30,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#EEE"),
            yaxis=dict(autorange="reversed"),
            showlegend=False
        )
        st.plotly_chart(fig_p, use_container_width=True)

    with col_d:
        st.markdown("##### Origen de contactos")
        orig = df_crm[df_crm["origen_contacto"].notna()]["origen_contacto"].value_counts().head(10).reset_index()
        orig.columns = ["origen","cantidad"]
        fig_o = go.Figure(go.Pie(
            labels=orig["origen"], values=orig["cantidad"],
            hole=0.4,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{value:,d}<extra></extra>"
        ))
        fig_o.update_layout(
            height=350, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False
        )
        st.plotly_chart(fig_o, use_container_width=True)

    st.divider()
    st.markdown("##### Leads validados — evolución mensual")

    if not df_lv.empty:
        df_lv = df_lv.copy()
        df_lv["fecha"] = pd.to_datetime(df_lv["fecha"], errors="coerce")
        df_lv = df_lv.dropna(subset=["fecha"])
        monthly = df_lv.groupby(df_lv["fecha"].dt.to_period("M"))["cantidad"].sum().reset_index()
        monthly["label"] = monthly["fecha"].apply(lambda p: periodo_label(p.to_timestamp()))
        monthly = monthly.sort_values("fecha")
        fig_lv = go.Figure(go.Bar(
            x=monthly["label"], y=monthly["cantidad"],
            marker_color=COLORES["positivo"],
            hovertemplate="<b>%{x}</b><br>Leads: %{y:,d}<extra></extra>"
        ))
        fig_lv.update_layout(
            height=280, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            showlegend=False
        )
        st.plotly_chart(fig_lv, use_container_width=True)
