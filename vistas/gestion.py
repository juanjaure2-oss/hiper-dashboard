import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.formato import num, ars, periodo_label

def _n(val):
    try:
        return float(str(val).replace(',','.').replace('$','').strip())
    except:
        return 0.0

def render(datos: dict, colores: dict):
    df_piezas    = datos.get("piezas",    pd.DataFrame())
    df_reuniones = datos.get("reuniones", pd.DataFrame())
    df_ppto      = datos.get("presupuesto", pd.DataFrame())
    df_tareas    = datos.get("tareas",    pd.DataFrame())

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("##### Piezas producidas")
        if df_piezas.empty:
            st.info("Sin datos de piezas.")
        else:
            df_piezas = df_piezas.copy()
            df_piezas["fecha"]    = pd.to_datetime(df_piezas["fecha"], errors="coerce")
            df_piezas["cantidad"] = df_piezas["cantidad"].apply(_n)
            por_area = df_piezas.groupby("area")["cantidad"].sum().reset_index().sort_values("cantidad", ascending=False)
            fig = go.Figure(go.Bar(
                x=por_area["cantidad"], y=por_area["area"],
                orientation="h", marker_color=colores["secundario"],
                text=por_area["cantidad"].apply(lambda x: str(int(x))), textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x} piezas<extra></extra>"
            ))
            fig.update_layout(
                height=220, margin=dict(l=0,r=40,t=10,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="#EEE"), yaxis=dict(autorange="reversed"), showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Total: {int(df_piezas['cantidad'].sum())} piezas")

    with col_b:
        st.markdown("##### Reuniones por tipo")
        if df_reuniones.empty:
            st.info("Sin datos de reuniones.")
        else:
            df_reuniones = df_reuniones.copy()
            df_reuniones["fecha"] = pd.to_datetime(df_reuniones["fecha"], errors="coerce")
            por_tipo = df_reuniones["tipo"].value_counts().reset_index()
            por_tipo.columns = ["tipo","cantidad"]
            fig_r = go.Figure(go.Pie(
                labels=por_tipo["tipo"], values=por_tipo["cantidad"],
                hole=0.4, textinfo="label+value",
                hovertemplate="<b>%{label}</b><br>%{value} reuniones<extra></extra>"
            ))
            fig_r.update_layout(
                height=220, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="rgba(0,0,0,0)", showlegend=False
            )
            st.plotly_chart(fig_r, use_container_width=True)
            st.caption(f"Total: {len(df_reuniones)} reuniones")

    st.divider()
    st.markdown("##### Evolución de gastos de marketing")
    if not df_ppto.empty:
        df_ppto = df_ppto.copy()
        df_ppto["fecha"] = pd.to_datetime(df_ppto["fecha"], errors="coerce")
        df_ppto = df_ppto.dropna(subset=["fecha"]).sort_values("fecha")
        for col in ["asesor_mkt","analista_comercial","agencia","inversiones","total_otros_gastos"]:
            if col in df_ppto.columns:
                df_ppto[col] = df_ppto[col].apply(_n)
        df_ppto["label"] = df_ppto["fecha"].apply(periodo_label)
        fig_p = go.Figure()
        for col, nombre, color in [
            ("asesor_mkt",         "Asesor MKT",         colores["primario"]),
            ("analista_comercial", "Analista Comercial",  colores["secundario"]),
            ("agencia",            "Agencia",             "#8E44AD"),
            ("inversiones",        "Inversiones/Eventos", "#E67E22"),
        ]:
            if col in df_ppto.columns:
                fig_p.add_trace(go.Bar(
                    x=df_ppto["label"], y=df_ppto[col],
                    name=nombre, marker_color=color,
                    hovertemplate=f"<b>%{{x}}</b><br>{nombre}: $%{{y:,.0f}}<extra></extra>"
                ))
        fig_p.update_layout(
            barmode="stack", height=300, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig_p, use_container_width=True)

    st.divider()
    st.markdown("##### Proyectos y tareas")
    if df_tareas.empty:
        st.info("Sin tareas cargadas.")
    else:
        df_t = df_tareas.copy()
        iconos = {"completada":"🟢","en_proceso":"🟡","pendiente":"🔴"}
        df_t["estado_fmt"] = df_t["estado"].map(iconos).fillna("⚪") + " " + df_t["estado"].fillna("—")
        filtros = ["Todos"] + sorted(df_t["estado"].dropna().unique().tolist())
        filtro  = st.selectbox("Filtrar por estado", filtros, key="tareas_filtro")
        if filtro != "Todos":
            df_t = df_t[df_t["estado"] == filtro]
        cols_show = [c for c in ["estado_fmt","proyecto","tarea","area","responsable","prioridad","fecha_vencimiento"] if c in df_t.columns]
        df_show = df_t[cols_show].rename(columns={"estado_fmt":"estado"})
        if "fecha_vencimiento" in df_show.columns:
            df_show["fecha_vencimiento"] = pd.to_datetime(df_show["fecha_vencimiento"], errors="coerce").dt.strftime("%d/%m/%Y")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
