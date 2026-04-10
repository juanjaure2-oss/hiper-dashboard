import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.config import COLORES


def _parse_fecha(df, col):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df


def render(datos: dict):
    df_piezas = datos.get("piezas", pd.DataFrame())
    df_reuniones = datos.get("reuniones", pd.DataFrame())
    df_tareas = datos.get("tareas", pd.DataFrame())

    periodos_set = set()

    # PIEZAS
    if not df_piezas.empty and "fecha" in df_piezas.columns:
        df_piezas = df_piezas.copy()
        df_piezas.columns = df_piezas.columns.str.strip().str.lower()
        df_piezas = _parse_fecha(df_piezas, "fecha")
        df_piezas = df_piezas.dropna(subset=["fecha"])
        if not df_piezas.empty:
            df_piezas["periodo"] = df_piezas["fecha"].dt.to_period("M")
            periodos_set.update(df_piezas["periodo"].dropna().unique())

    # REUNIONES
    if not df_reuniones.empty and "fecha" in df_reuniones.columns:
        df_reuniones = df_reuniones.copy()
        df_reuniones.columns = df_reuniones.columns.str.strip().str.lower()
        df_reuniones = _parse_fecha(df_reuniones, "fecha")
        df_reuniones = df_reuniones.dropna(subset=["fecha"])
        if not df_reuniones.empty:
            df_reuniones["periodo"] = df_reuniones["fecha"].dt.to_period("M")
            periodos_set.update(df_reuniones["periodo"].dropna().unique())

    # TAREAS
    if not df_tareas.empty:
        df_tareas = df_tareas.copy()
        df_tareas.columns = df_tareas.columns.str.strip().str.lower()

        for c in ["fecha_inicio", "fecha_vencimiento", "fecha"]:
            df_tareas = _parse_fecha(df_tareas, c)

        periodo_vto = df_tareas["fecha_vencimiento"].dt.to_period("M") if "fecha_vencimiento" in df_tareas.columns else None
        periodo_ini = df_tareas["fecha_inicio"].dt.to_period("M") if "fecha_inicio" in df_tareas.columns else None
        periodo_fecha = df_tareas["fecha"].dt.to_period("M") if "fecha" in df_tareas.columns else None

        if periodo_vto is not None:
            df_tareas["periodo_ref"] = periodo_vto
        else:
            df_tareas["periodo_ref"] = pd.Series([pd.NaT] * len(df_tareas), index=df_tareas.index, dtype="object")

        if periodo_ini is not None:
            df_tareas["periodo_ref"] = df_tareas["periodo_ref"].combine_first(periodo_ini)

        if periodo_fecha is not None:
            df_tareas["periodo_ref"] = df_tareas["periodo_ref"].combine_first(periodo_fecha)

        periodos_set.update(df_tareas["periodo_ref"].dropna().unique())

    if not periodos_set:
        st.warning("Sin datos de gestión.")
        return

    periodos = sorted(periodos_set, reverse=True)
    labels_periodos = [str(p) for p in periodos]

    st.markdown("##### Gestión")
    sel = st.selectbox("Período", labels_periodos, index=0, key="gestion_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    # FILTROS DEL MES
    df_piezas_mes = df_piezas[df_piezas["periodo"] == periodo_sel].copy() if not df_piezas.empty and "periodo" in df_piezas.columns else pd.DataFrame()
    df_reuniones_mes = df_reuniones[df_reuniones["periodo"] == periodo_sel].copy() if not df_reuniones.empty and "periodo" in df_reuniones.columns else pd.DataFrame()
    df_tareas_mes = df_tareas[df_tareas["periodo_ref"] == periodo_sel].copy() if not df_tareas.empty and "periodo_ref" in df_tareas.columns else pd.DataFrame()

    # KPIs
    piezas_total = pd.to_numeric(df_piezas_mes["cantidad"], errors="coerce").fillna(0).sum() if not df_piezas_mes.empty and "cantidad" in df_piezas_mes.columns else 0
    reuniones_total = len(df_reuniones_mes)

    tareas_abiertas = 0
    tareas_completadas = 0
    tareas_vencidas = 0

    if not df_tareas_mes.empty:
        if "estado" in df_tareas_mes.columns:
            estado_mes = df_tareas_mes["estado"].fillna("pendiente").astype(str).str.lower().str.strip()
        else:
            estado_mes = pd.Series(["pendiente"] * len(df_tareas_mes), index=df_tareas_mes.index)

        tareas_abiertas = int((estado_mes != "completada").sum())
        tareas_completadas = int((estado_mes == "completada").sum())

        if "fecha_vencimiento" in df_tareas_mes.columns:
            hoy = pd.Timestamp.today().normalize()
            tareas_vencidas = int(
                (
                    df_tareas_mes["fecha_vencimiento"].notna()
                    & (df_tareas_mes["fecha_vencimiento"] < hoy)
                    & (estado_mes != "completada")
                ).sum()
            )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Piezas del período", int(piezas_total))
    c2.metric("Reuniones del período", int(reuniones_total))
    c3.metric("Tareas abiertas", int(tareas_abiertas))
    c4.metric("Tareas vencidas", int(tareas_vencidas))

    st.divider()

    # REUNIONES + PIEZAS
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

    # TABLERO DE TAREAS
    st.markdown("##### Proyectos y tareas del período")

    if df_tareas.empty:
        st.info("Sin tareas cargadas.")
        return

    estado_color = {
        "completada": "🟢",
        "en_proceso": "🟡",
        "pendiente": "🔴",
    }

    if "estado" not in df_tareas.columns:
        df_tareas["estado"] = "pendiente"

    df_tareas["estado"] = df_tareas["estado"].fillna("pendiente").astype(str).str.lower().str.strip()
    df_tareas["est_icon"] = df_tareas["estado"].map(estado_color).fillna("⚪")
    df_tareas["estado_fmt"] = df_tareas["est_icon"] + " " + df_tareas["estado"]

    df_t_view = df_tareas_mes.copy() if not df_tareas_mes.empty else df_tareas.copy()

    if "estado_fmt" not in df_t_view.columns:
        if "estado" not in df_t_view.columns:
            df_t_view["estado"] = "pendiente"
        df_t_view["estado"] = df_t_view["estado"].fillna("pendiente").astype(str).str.lower().str.strip()
        df_t_view["est_icon"] = df_t_view["estado"].map(estado_color).fillna("⚪")
        df_t_view["estado_fmt"] = df_t_view["est_icon"] + " " + df_t_view["estado"]

    estados_disp = ["Todos"] + sorted(df_t_view["estado"].dropna().unique().tolist())
    filtro_estado = st.selectbox("Filtrar por estado", estados_disp, key="tareas_filtro_estado")

    if filtro_estado != "Todos":
        df_t_view = df_t_view[df_t_view["estado"] == filtro_estado].copy()

    colx1, colx2 = st.columns(2)
    with colx1:
        st.markdown(f"**Tareas mostradas:** {len(df_t_view)}")
    with colx2:
        completadas_view = int((df_t_view["estado"] == "completada").sum()) if "estado" in df_t_view.columns else 0
        st.markdown(f"**Completadas:** {completadas_view}")

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
            df_show[c] = df_show[c].fillna("")

    st.dataframe(df_show, use_container_width=True, hide_index=True)
