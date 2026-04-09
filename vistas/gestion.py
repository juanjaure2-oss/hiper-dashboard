import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import num, periodo_label
from utils.config import COLORES


def _parse_fecha(df, col):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df


def render(datos: dict):
    df_piezas = datos.get("piezas", pd.DataFrame())
    df_reuniones = datos.get("reuniones", pd.DataFrame())
    df_tareas = datos.get("tareas", pd.DataFrame())

    # =========================
    # PREPARACIÓN DE PERÍODOS
    # =========================
    periodos_set = set()

    if not df_piezas.empty and "fecha" in df_piezas.columns:
        df_piezas = df_piezas.copy()
        df_piezas = _parse_fecha(df_piezas, "fecha")
        df_piezas = df_piezas.dropna(subset=["fecha"])
        if not df_piezas.empty:
            df_piezas["periodo"] = df_piezas["fecha"].dt.to_period("M")
            periodos_set.update(df_piezas["periodo"].dropna().unique())

    if not df_reuniones.empty and "fecha" in df_reuniones.columns:
        df_reuniones = df_reuniones.copy()
        df_reuniones = _parse_fecha(df_reuniones, "fecha")
        df_reuniones = df_reuniones.dropna(subset=["fecha"])
        if not df_reuniones.empty:
            df_reuniones["periodo"] = df_reuniones["fecha"].dt.to_period("M")
            periodos_set.update(df_reuniones["periodo"].dropna().unique())

    if not df_tareas.empty:
        df_tareas = df_tareas.copy()
        for c in ["fecha_inicio", "fecha_vencimiento", "fecha"]:
            df_tareas = _parse_fecha(df_tareas, c)

        # priorizamos fecha_vencimiento, si no fecha_inicio, si no fecha
        if "fecha_vencimiento" in df_tareas.columns and df_tareas["fecha_vencimiento"].notna().any():
            df_tareas["periodo_ref"] = df_tareas["fecha_vencimiento"].dt.to_period("M")
        elif "fecha_inicio" in df_tareas.columns and df_tareas["fecha_inicio"].notna().any():
            df_tareas["periodo_ref"] = df_tareas["fecha_inicio"].dt.to_period("M")
        elif "fecha" in df_tareas.columns and df_tareas["fecha"].notna().any():
            df_tareas["periodo_ref"] = df_tareas["fecha"].dt.to_period("M")
        else:
            df_tareas["periodo_ref"] = pd.NaT

        periodos_set.update([p for p in df_tareas["periodo_ref"].dropna().unique()])

    if not periodos_set:
        st.warning("Sin datos de gestión.")
        return

    periodos = sorted(periodos_set, reverse=True)
    labels_periodos = [str(p) for p in periodos]

    st.markdown("##### Gestión")
    sel = st.selectbox("Período", labels_periodos, index=0, key="gestion_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    # =========================
    # FILTROS DEL MES
    # =========================
    df_piezas_mes = pd.DataFrame()
    if not df_piezas.empty and "periodo" in df_piezas.columns:
        df_piezas_mes = df_piezas[df_piezas["periodo"] == periodo_sel].copy()

    df_reuniones_mes = pd.DataFrame()
    if not df_reuniones.empty and "periodo" in df_reuniones.columns:
        df_reuniones_mes = df_reuniones[df_reuniones["periodo"] == periodo_sel].copy()

    df_tareas_mes = pd.DataFrame()
    if not df_tareas.empty and "periodo_ref" in df_tareas.columns:
        df_tareas_mes = df_tareas[df_tareas["periodo_ref"] == periodo_sel].copy()

    # =========================
    # KPIs DEL PERÍODO
    # =========================
    piezas_total = 0
    if not df_piezas_mes.empty and "cantidad" in df_piezas_mes.columns:
        piezas_total = pd.to_numeric(df_piezas_mes["cantidad"], errors="coerce").fillna(0).sum()

    reuniones_total = len(df_reuniones_mes)

    tareas_abiertas = 0
    tareas_completadas = 0
    tareas_vencidas = 0

    if not df_tareas_mes.empty:
        estado = df_tareas_mes["estado"].astype(str).str.lower().str.strip() if "estado" in df_tareas_mes.columns else pd.Series(dtype="object")
        tareas_abiertas = (estado != "completada").sum() if not estado.empty else len(df_tareas_mes)
        tareas_completadas = (estado == "completada").sum() if not estado.empty else 0

        if "fecha_vencimiento" in df_tareas_mes.columns:
            hoy = pd.Timestamp.today().normalize()
            tareas_vencidas = df_tareas_mes[
                (df_tareas_mes["fecha_vencimiento"].notna()) &
                (df_tareas_mes["fecha_vencimiento"] < hoy) &
                (estado != "completada")
            ].shape[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Piezas del período", int(piezas_total))
    c2.metric("Reuniones del período", int(reuniones_total))
    c3.metric("Tareas abiertas", int(tareas_abiertas))
    c4.metric("Tareas vencidas", int(tareas_vencidas))

    st.divider()

    # =========================
    # REUNIONES + PIEZAS
    # =========================
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("##### Reuniones por tipo")

        if df_reuniones_mes.empty or "tipo" not in df_reuniones_mes.columns:
            st.info("Sin reuniones para el período seleccionado.")
        else:
            por_tipo = (
                df_reuniones_mes["tipo"]
                .fillna("Sin tipo")
                .astype(str)
                .str.strip()
                .value_counts()
                .reset_index()
            )
            por_tipo.columns = ["tipo", "cantidad"]

            fig_r = go.Figure(
                go.Bar(
                    x=por_tipo["cantidad"],
                    y=por_tipo["tipo"],
                    orientation="h",
                    marker_color=COLORES["primario"],
                    text=por_tipo["cantidad"],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x} reuniones<extra></extra>",
                )
            )
            fig_r.update_layout(
                height=340,
                margin=dict(l=0, r=40, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="#EEE"),
                yaxis=dict(autorange="reversed"),
                showlegend=False,
            )
            st.plotly_chart(fig_r, use_container_width=True)

    with col_b:
        st.markdown("##### Piezas por área")

        if df_piezas_mes.empty or "area" not in df_piezas_mes.columns or "cantidad" not in df_piezas_mes.columns:
            st.info("Sin piezas para el período seleccionado.")
        else:
            df_piezas_mes["cantidad"] = pd.to_numeric(df_piezas_mes["cantidad"], errors="coerce").fillna(0)

            por_area = (
                df_piezas_mes.groupby("area", as_index=False)["cantidad"]
                .sum()
                .sort_values("cantidad", ascending=False)
            )

            fig_p = go.Figure(
                go.Bar(
                    x=por_area["cantidad"],
                    y=por_area["area"],
                    orientation="h",
                    marker_color=COLORES["secundario"],
                    text=por_area["cantidad"],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>%{x} piezas<extra></extra>",
                )
            )
            fig_p.update_layout(
                height=340,
                margin=dict(l=0, r=40, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="#EEE"),
                yaxis=dict(autorange="reversed"),
                showlegend=False,
            )
            st.plotly_chart(fig_p, use_container_width=True)

    st.divider()

    # =========================
    # TABLERO DE TAREAS
    # =========================
    st.markdown("##### Proyectos y tareas del período")

    if df_tareas.empty:
        st.info("Sin tareas cargadas.")
        return

    df_t = df_tareas.copy()

    estado_color = {
        "completada": "🟢",
        "en_proceso": "🟡",
        "pendiente": "🔴",
    }

    if "estado" not in df_t.columns:
        df_t["estado"] = "sin_estado"

    df_t["estado"] = df_t["estado"].fillna("sin_estado").astype(str).str.lower().str.strip()
    df_t["est_icon"] = df_t["estado"].map(estado_color).fillna("⚪")
    df_t["estado_fmt"] = df_t["est_icon"] + " " + df_t["estado"]

    # filtro principal por estado
    estados_disp = ["Todos"] + sorted(df_t["estado"].dropna().unique().tolist())
    filtro_estado = st.selectbox("Filtrar por estado", estados_disp, key="tareas_filtro_estado")

    # trabajamos sobre tareas del período
    df_t_view = df_t_mes.copy() if not df_tareas_mes.empty else df_t.copy()

    if filtro_estado != "Todos":
        df_t_view = df_t_view[df_t_view["estado"] == filtro_estado]

    # resumen rápido
    colx1, colx2 = st.columns(2)
    with colx1:
        st.markdown(f"**Tareas del período:** {len(df_t_view)}")
    with colx2:
        completadas = (df_t_view["estado"] == "completada").sum() if "estado" in df_t_view.columns else 0
        st.markdown(f"**Completadas del período:** {int(completadas)}")

    cols_show = [
        "estado_fmt",
        "proyecto",
        "tarea",
        "area",
        "responsable",
        "prioridad",
        "fecha_inicio",
        "fecha_vencimiento",
    ]
    cols_show = [c for c in cols_show if c in df_t_view.columns]

    df_show = df_t_view[cols_show].copy().rename(columns={"estado_fmt": "estado"})

    for c in ["fecha_inicio", "fecha_vencimiento"]:
        if c in df_show.columns:
            df_show[c] = pd.to_datetime(df_show[c], errors="coerce").dt.strftime("%d/%m/%Y")

    st.dataframe(df_show, use_container_width=True, hide_index=True)
