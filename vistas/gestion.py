import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.config import COLORES


def _parse_fecha(df, col):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df


def _safe_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out.columns = out.columns.str.strip().str.lower()
    return out


def render(datos: dict):
    df_piezas = _safe_cols(datos.get("piezas", pd.DataFrame()))
    df_reuniones = _safe_cols(datos.get("reuniones", pd.DataFrame()))
    df_tareas = _safe_cols(datos.get("tareas", pd.DataFrame()))

    # =========================
    # PREPARACIÓN DE DATOS
    # =========================
    periodos_set = set()

    # PIEZAS
    if not df_piezas.empty and "fecha" in df_piezas.columns:
        df_piezas = _parse_fecha(df_piezas, "fecha")
        df_piezas = df_piezas.dropna(subset=["fecha"])
        if not df_piezas.empty:
            df_piezas["periodo"] = df_piezas["fecha"].dt.to_period("M")
            periodos_set.update(df_piezas["periodo"].dropna().unique())

    # REUNIONES
    if not df_reuniones.empty and "fecha" in df_reuniones.columns:
        df_reuniones = _parse_fecha(df_reuniones, "fecha")
        df_reuniones = df_reuniones.dropna(subset=["fecha"])
        if not df_reuniones.empty:
            df_reuniones["periodo"] = df_reuniones["fecha"].dt.to_period("M")
            periodos_set.update(df_reuniones["periodo"].dropna().unique())

    # TAREAS
    if not df_tareas.empty:
        for c in ["fecha_inicio", "fecha_vencimiento", "fecha"]:
            df_tareas = _parse_fecha(df_tareas, c)

        if "estado" not in df_tareas.columns:
            df_tareas["estado"] = "pendiente"
        df_tareas["estado"] = (
            df_tareas["estado"]
            .fillna("pendiente")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        # Normalización flexible de estados
        mapa_estado = {
            "completado": "completada",
            "completa": "completada",
            "hecho": "completada",
            "done": "completada",
            "en proceso": "en_proceso",
            "en-proceso": "en_proceso",
            "progreso": "en_proceso",
            "in progress": "en_proceso",
            "pendiente": "pendiente",
            "to do": "pendiente",
            "todo": "pendiente",
        }
        df_tareas["estado"] = df_tareas["estado"].replace(mapa_estado)

        # Áreas / responsables / proyecto como texto limpio
        for c in ["area", "responsable", "proyecto", "tarea", "prioridad", "observaciones"]:
            if c in df_tareas.columns:
                df_tareas[c] = df_tareas[c].fillna("").astype(str).str.strip()

        # Períodos posibles para tareas, solo para alimentar selectores si hiciera falta
        for c in ["fecha_inicio", "fecha_vencimiento", "fecha"]:
            if c in df_tareas.columns:
                periodos_set.update(df_tareas[c].dropna().dt.to_period("M").unique())

    if not periodos_set:
        st.warning("Sin datos de gestión.")
        return

    periodos = sorted(periodos_set, reverse=True)
    labels_periodos = [str(p) for p in periodos]

    st.markdown("##### Gestión")
    sel = st.selectbox("Período general", labels_periodos, index=0, key="gestion_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    # =========================
    # FILTROS DEL MES PARA PIEZAS Y REUNIONES
    # =========================
    df_piezas_mes = pd.DataFrame()
    if not df_piezas.empty and "periodo" in df_piezas.columns:
        df_piezas_mes = df_piezas[df_piezas["periodo"] == periodo_sel].copy()

    df_reuniones_mes = pd.DataFrame()
    if not df_reuniones.empty and "periodo" in df_reuniones.columns:
        df_reuniones_mes = df_reuniones[df_reuniones["periodo"] == periodo_sel].copy()

    # =========================
    # KPIs PIEZAS + REUNIONES
    # =========================
    piezas_total = 0
    if not df_piezas_mes.empty and "cantidad" in df_piezas_mes.columns:
        piezas_total = pd.to_numeric(df_piezas_mes["cantidad"], errors="coerce").fillna(0).sum()

    reuniones_total = len(df_reuniones_mes)

    # =========================
    # KPIs TAREAS (globales filtrables)
    # =========================
    tareas_abiertas = 0
    tareas_completadas = 0
    tareas_vencidas = 0

    if not df_tareas.empty:
        hoy = pd.Timestamp.today().normalize()
        estado_all = df_tareas["estado"]

        tareas_abiertas = int((estado_all != "completada").sum())
        tareas_completadas = int((estado_all == "completada").sum())

        if "fecha_vencimiento" in df_tareas.columns:
            tareas_vencidas = int(
                (
                    df_tareas["fecha_vencimiento"].notna()
                    & (df_tareas["fecha_vencimiento"] < hoy)
                    & (estado_all != "completada")
                ).sum()
            )

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
    # TAREAS
    # =========================
    st.markdown("##### Proyectos y tareas")

    if df_tareas.empty:
        st.info("Sin tareas cargadas.")
        return

    estado_color = {
        "completada": "🟢",
        "en_proceso": "🟡",
        "pendiente": "🔴",
    }

    # ----- Filtros de tareas -----
    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        estados_disp = ["Todos"] + sorted(df_tareas["estado"].dropna().unique().tolist())
        filtro_estado = st.selectbox("Estado", estados_disp, key="tareas_filtro_estado")

    with colf2:
        areas_disp = ["Todas"]
        if "area" in df_tareas.columns:
            areas_disp += sorted([x for x in df_tareas["area"].dropna().unique().tolist() if x])
        filtro_area = st.selectbox("Área", areas_disp, key="tareas_filtro_area")

    with colf3:
        resp_disp = ["Todos"]
        if "responsable" in df_tareas.columns:
            resp_disp += sorted([x for x in df_tareas["responsable"].dropna().unique().tolist() if x])
        filtro_resp = st.selectbox("Responsable", resp_disp, key="tareas_filtro_resp")

    with colf4:
        proyectos_disp = ["Todos"]
        if "proyecto" in df_tareas.columns:
            proyectos_disp += sorted([x for x in df_tareas["proyecto"].dropna().unique().tolist() if x])
        filtro_proyecto = st.selectbox("Proyecto", proyectos_disp, key="tareas_filtro_proyecto")

    colf5, colf6, colf7 = st.columns([2, 2, 2])

    with colf5:
        criterio_fecha = st.selectbox(
            "Filtrar por fecha",
            ["todas", "fecha_inicio", "fecha_vencimiento"],
            key="tareas_criterio_fecha",
        )

    # armado de rango sugerido
    fecha_min = None
    fecha_max = None
    for c in ["fecha_inicio", "fecha_vencimiento"]:
        if c in df_tareas.columns and df_tareas[c].notna().any():
            cmin = df_tareas[c].min()
            cmax = df_tareas[c].max()
            fecha_min = cmin if fecha_min is None else min(fecha_min, cmin)
            fecha_max = cmax if fecha_max is None else max(fecha_max, cmax)

    with colf6:
        usar_rango = st.checkbox("Usar rango de fechas", value=False, key="tareas_usar_rango")

    fecha_desde = None
    fecha_hasta = None
    if usar_rango and fecha_min is not None and fecha_max is not None:
        with colf7:
            rango = st.date_input(
                "Rango",
                value=(fecha_min.date(), fecha_max.date()),
                min_value=fecha_min.date(),
                max_value=fecha_max.date(),
                key="tareas_rango",
            )
        if isinstance(rango, tuple) and len(rango) == 2:
            fecha_desde = pd.Timestamp(rango[0])
            fecha_hasta = pd.Timestamp(rango[1])

    # ----- DataFrame filtrado -----
    df_t_view = df_tareas.copy()

    if filtro_estado != "Todos":
        df_t_view = df_t_view[df_t_view["estado"] == filtro_estado].copy()

    if filtro_area != "Todas" and "area" in df_t_view.columns:
        df_t_view = df_t_view[df_t_view["area"] == filtro_area].copy()

    if filtro_resp != "Todos" and "responsable" in df_t_view.columns:
        df_t_view = df_t_view[df_t_view["responsable"] == filtro_resp].copy()

    if filtro_proyecto != "Todos" and "proyecto" in df_t_view.columns:
        df_t_view = df_t_view[df_t_view["proyecto"] == filtro_proyecto].copy()

    if usar_rango and criterio_fecha != "todas" and criterio_fecha in df_t_view.columns and fecha_desde is not None and fecha_hasta is not None:
        df_t_view = df_t_view[
            df_t_view[criterio_fecha].notna()
            & (df_t_view[criterio_fecha] >= fecha_desde)
            & (df_t_view[criterio_fecha] <= fecha_hasta)
        ].copy()

    # ----- Estados visuales -----
    df_t_view["est_icon"] = df_t_view["estado"].map(estado_color).fillna("⚪")
    df_t_view["estado_fmt"] = df_t_view["est_icon"] + " " + df_t_view["estado"]

    # vencida dinámica
    hoy = pd.Timestamp.today().normalize()
    if "fecha_vencimiento" in df_t_view.columns:
        df_t_view["vencida"] = (
            df_t_view["fecha_vencimiento"].notna()
            & (df_t_view["fecha_vencimiento"] < hoy)
            & (df_t_view["estado"] != "completada")
        )
    else:
        df_t_view["vencida"] = False

    # ----- Resumen -----
    colx1, colx2, colx3 = st.columns(3)
    with colx1:
        st.markdown(f"**Tareas mostradas:** {len(df_t_view)}")
    with colx2:
        completadas_view = int((df_t_view["estado"] == "completada").sum()) if "estado" in df_t_view.columns else 0
        st.markdown(f"**Completadas:** {completadas_view}")
    with colx3:
        vencidas_view = int(df_t_view["vencida"].sum()) if "vencida" in df_t_view.columns else 0
        st.markdown(f"**Vencidas:** {vencidas_view}")

    # ----- Tabla -----
    cols_show = [
        "estado_fmt",
        "proyecto",
        "tarea",
        "area",
        "responsable",
        "prioridad",
        "fecha_inicio",
        "fecha_vencimiento",
        "vencida",
    ]
    cols_show = [c for c in cols_show if c in df_t_view.columns]

    df_show = df_t_view[cols_show].copy().rename(
        columns={
            "estado_fmt": "estado",
            "fecha_inicio": "inicio",
            "fecha_vencimiento": "vencimiento",
        }
    )

    for c in ["inicio", "vencimiento"]:
        if c in df_show.columns:
            df_show[c] = pd.to_datetime(df_show[c], errors="coerce").dt.strftime("%d/%m/%Y")
            df_show[c] = df_show[c].fillna("")

    if "vencida" in df_show.columns:
        df_show["vencida"] = df_show["vencida"].map({True: "Sí", False: ""})

    st.dataframe(df_show, use_container_width=True, hide_index=True)
