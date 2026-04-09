import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import periodo_label
from utils.config import COLORES


def render(datos: dict):
    df_piezas    = datos.get("piezas", pd.DataFrame())
    df_reuniones = datos.get("reuniones", pd.DataFrame())
    df_tareas    = datos.get("tareas", pd.DataFrame())
    periodo      = datos.get("periodo")

    # =========================
    # KPI SUPERIOR
    # =========================
    col1, col2, col3 = st.columns(3)

    piezas_total = 0
    reuniones_total = 0
    tareas_abiertas = 0

    # PIEZAS KPI
    if not df_piezas.empty:
        df_piezas["fecha"] = pd.to_datetime(df_piezas["fecha"], errors="coerce")
        df_piezas = df_piezas.dropna(subset=["fecha"])
        df_piezas["periodo"] = df_piezas["fecha"].dt.to_period("M")

        if periodo:
            df_piezas = df_piezas[df_piezas["periodo"] == periodo]

        piezas_total = df_piezas["cantidad"].sum()

    # REUNIONES KPI
    if not df_reuniones.empty:
        df_reuniones["fecha"] = pd.to_datetime(df_reuniones["fecha"], errors="coerce")
        df_reuniones = df_reuniones.dropna(subset=["fecha"])
        df_reuniones["periodo"] = df_reuniones["fecha"].dt.to_period("M")

        if periodo:
            df_reuniones = df_reuniones[df_reuniones["periodo"] == periodo]

        reuniones_total = len(df_reuniones)

    # TAREAS KPI
    if not df_tareas.empty:
        tareas_abiertas = df_tareas[df_tareas["estado"] != "completada"].shape[0]

    col1.metric("Piezas del período", int(piezas_total))
    col2.metric("Reuniones del período", reuniones_total)
    col3.metric("Tareas abiertas", tareas_abiertas)

    st.divider()

    # =========================
    # PIEZAS + REUNIONES
    # =========================
    col_a, col_b = st.columns(2)

    # PIEZAS
    with col_a:
        st.markdown("##### Piezas por área")

        if df_piezas.empty:
            st.info("Sin datos.")
        else:
            por_area = (
                df_piezas.groupby("area")["cantidad"]
                .sum()
                .reset_index()
                .sort_values("cantidad", ascending=False)
            )

            fig = go.Figure(go.Bar(
                x=por_area["cantidad"],
                y=por_area["area"],
                orientation="h",
                marker_color=COLORES["secundario"],
                text=por_area["cantidad"],
                textposition="outside"
            ))

            fig.update_layout(
                height=250,
                margin=dict(l=0,r=40,t=10,b=0),
                yaxis=dict(autorange="reversed"),
                paper_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(fig, use_container_width=True)

    # REUNIONES
    with col_b:
        st.markdown("##### Reuniones por tipo")

        if df_reuniones.empty:
            st.info("Sin datos.")
        else:
            por_tipo = df_reuniones["tipo"].value_counts()

            fig = go.Figure(go.Pie(
                labels=por_tipo.index,
                values=por_tipo.values,
                hole=0.4
            ))

            fig.update_layout(height=250)

            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =========================
    # EVOLUCIÓN HISTÓRICA
    # =========================
    st.markdown("##### Evolución de actividad")

    if not df_piezas.empty:
        df_hist = df_piezas.copy()
        df_hist = df_hist.groupby("periodo")["cantidad"].sum().reset_index()
        df_hist["label"] = df_hist["periodo"].astype(str)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_hist["label"],
            y=df_hist["cantidad"],
            mode="lines+markers",
            name="Piezas",
            line=dict(color=COLORES["primario"])
        ))

        fig.update_layout(
            height=280,
            xaxis=dict(tickangle=-45),
            paper_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =========================
    # TAREAS
    # =========================
    st.markdown("##### Tablero de tareas")

    if df_tareas.empty:
        st.info("Sin tareas.")
        return

    df_t = df_tareas.copy()

    estado_color = {
        "completada":  "🟢",
        "en_proceso":  "🟡",
        "pendiente":   "🔴",
    }

    df_t["estado_icono"] = df_t["estado"].map(estado_color).fillna("⚪")
    df_t["estado_fmt"] = df_t["estado_icono"] + " " + df_t["estado"].fillna("—")

    # KPIs tareas
    col1, col2 = st.columns(2)

    abiertas = df_t[df_t["estado"] != "completada"].shape[0]
    completadas = df_t[df_t["estado"] == "completada"].shape[0]

    col1.metric("Abiertas", abiertas)
    col2.metric("Completadas", completadas)

    # FILTRO
    estados = ["Todos"] + sorted(df_t["estado"].dropna().unique().tolist())
    filtro = st.selectbox("Filtrar por estado", estados)

    if filtro != "Todos":
        df_t = df_t[df_t["estado"] == filtro]

    cols = ["estado_fmt","proyecto","tarea","area","responsable","prioridad","fecha_vencimiento"]
    cols = [c for c in cols if c in df_t.columns]

    df_show = df_t[cols].rename(columns={"estado_fmt":"estado"})

    if "fecha_vencimiento" in df_show.columns:
        df_show["fecha_vencimiento"] = pd.to_datetime(
            df_show["fecha_vencimiento"],
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

    st.dataframe(df_show, use_container_width=True, hide_index=True)
