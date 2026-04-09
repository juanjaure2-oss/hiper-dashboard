import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.formato import ars, num, periodo_label, variacion
from utils.config import COLORES

def render(datos: dict):
    df_v = datos.get("ventas", pd.DataFrame())
    df_kpi = datos.get("kpi", pd.DataFrame())

    if df_v.empty:
        st.warning("Sin datos de ventas.")
        return

    df_v = df_v.copy()
    df_v["fecha"] = pd.to_datetime(df_v["fecha"], errors="coerce")
    df_v = df_v.dropna(subset=["fecha"])
    df_v["periodo"] = df_v["fecha"].dt.to_period("M")
    df_v["label"] = df_v["fecha"].apply(lambda x: periodo_label(x) if pd.notna(x) else "")

    # Filtro de período
    periodos = sorted(df_v["periodo"].unique(), reverse=True)
    periodo_labels = [str(p) for p in periodos]
    col_f1, col_f2 = st.columns([3,1])
    with col_f1:
        sel = st.selectbox("Período", options=periodo_labels, index=0, key="ventas_periodo")
    periodo_sel = pd.Period(sel, freq="M")

    st.divider()

    # KPIs del período seleccionado
    df_mes = df_v[df_v["periodo"] == periodo_sel]
    df_mes_ant = df_v[df_v["periodo"] == (periodo_sel - 1)]

    total_mes = df_mes["total"].sum() if not df_mes.empty else 0
    total_ant = df_mes_ant["total"].sum() if not df_mes_ant.empty else 0
    zing_mes  = df_mes["zingueria"].sum() if not df_mes.empty else 0
    perf_mes  = df_mes["perfileria"].sum() if not df_mes.empty else 0
    cant_mes  = df_mes["cantidad"].sum() if not df_mes.empty else 0

    dv, delta_str = variacion(total_mes, total_ant)

    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.metric("Facturación total", ars(total_mes), delta_str)
    with c2:
        st.metric("Zinguería", ars(zing_mes))
    with c3:
        st.metric("Perfilería", ars(perf_mes))
    with c4:
        st.metric("Transacciones", num(cant_mes))

    st.divider()

    col_a, col_b = st.columns([2,1])

    with col_a:
        st.markdown("##### Evolución mensual de ventas")
        df_monthly = df_v.groupby("periodo").agg(
            total=("total","sum"),
            zingueria=("zingueria","sum"),
            perfileria=("perfileria","sum"),
        ).reset_index().sort_values("periodo")
        df_monthly["label"] = df_monthly["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_monthly["label"], y=df_monthly["zingueria"],
            name="Zinguería", marker_color=COLORES["primario"],
            hovertemplate="<b>%{x}</b><br>Zinguería: $%{y:,.0f}<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=df_monthly["label"], y=df_monthly["perfileria"],
            name="Perfilería", marker_color=COLORES["secundario"],
            hovertemplate="<b>%{x}</b><br>Perfilería: $%{y:,.0f}<extra></extra>"
        ))
        fig.update_layout(
            barmode="stack", height=320,
            margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("##### Mix del período")
        if zing_mes + perf_mes > 0:
            fig_pie = go.Figure(go.Pie(
                labels=["Zinguería","Perfilería"],
                values=[zing_mes, perf_mes],
                marker_colors=[COLORES["primario"], COLORES["secundario"]],
                hole=0.45,
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>"
            ))
            fig_pie.update_layout(
                height=280, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="rgba(0,0,0,0)", showlegend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos de líneas para este período.")

    # Top clientes del período
    if not df_mes.empty:
        st.markdown("##### Top clientes del período")
        top = df_mes.groupby("cliente")["total"].sum().sort_values(ascending=False).head(10).reset_index()
        top["total_fmt"] = top["total"].apply(ars)
        fig_h = go.Figure(go.Bar(
            x=top["total"], y=top["cliente"],
            orientation="h",
            marker_color=COLORES["primario"],
            text=top["total_fmt"], textposition="outside",
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>"
        ))
        fig_h.update_layout(
            height=max(250, len(top)*35),
            margin=dict(l=0,r=80,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            yaxis=dict(autorange="reversed"),
            showlegend=False
        )
        st.plotly_chart(fig_h, use_container_width=True)

    # Tabla detalle
    with st.expander("Ver detalle de transacciones"):
        df_show = df_mes[["fecha","cliente","cantidad","zingueria","perfileria","total"]].copy()
        df_show["fecha"] = df_show["fecha"].dt.strftime("%d/%m/%Y")
        for col in ["zingueria","perfileria","total"]:
            df_show[col] = df_show[col].apply(lambda x: ars(x) if pd.notna(x) else "—")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
