import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.formato import ars, num, periodo_label, variacion_pct
from utils.config import get_lineas_venta

def _n(val):
    try:
        if isinstance(val, (int, float)):
            return float(val) if not np.isnan(float(val)) else 0.0
        s = str(val).strip().replace("$","").replace(" ","")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif s.count(".") > 1:
            s = s.replace(".", "")
        return float(s) if s not in ("", "-", "N/A") else 0.0
    except:
        return 0.0

def render(datos: dict, colores: dict, empresa: str = ""):
    df_v = datos.get("ventas", pd.DataFrame())
    if df_v.empty:
        st.warning("Sin datos de ventas.")
        return

    # Líneas de venta configuradas para esta empresa
    lineas, labels = get_lineas_venta(empresa)
    tiene_lineas = len(lineas) > 0 and all(c in df_v.columns for c in lineas)

    df_v = df_v.copy()
    df_v["fecha"] = pd.to_datetime(df_v["fecha"], errors="coerce")
    df_v = df_v.dropna(subset=["fecha"])

    # Convertir numéricas
    cols_num = ["total", "cantidad"] + lineas
    for col in cols_num:
        if col in df_v.columns:
            df_v[col] = df_v[col].apply(_n)

    df_v["periodo"] = df_v["fecha"].dt.to_period("M")
    periodos = sorted(df_v["periodo"].unique(), reverse=True)
    if not periodos:
        st.warning("Sin períodos disponibles.")
        return

    sel = st.selectbox("Período", [str(p) for p in periodos], index=0, key="ventas_periodo")
    periodo_sel = pd.Period(sel, freq="M")
    st.divider()

    df_mes     = df_v[df_v["periodo"] == periodo_sel]
    df_mes_ant = df_v[df_v["periodo"] == (periodo_sel - 1)]

    total_mes = float(df_mes["total"].sum())     if not df_mes.empty else 0
    total_ant = float(df_mes_ant["total"].sum()) if not df_mes_ant.empty else 0
    cant_mes  = float(df_mes["cantidad"].sum())  if not df_mes.empty and "cantidad" in df_mes.columns else 0

    dv = variacion_pct(total_mes, total_ant)
    delta_str = f"{'▲' if dv and dv>=0 else '▼'} {abs(dv)*100:.1f}% vs mes anterior" if dv else ""

    # ── Métricas ──────────────────────────────────────────────
    if tiene_lineas:
        linea_vals = {l: float(df_mes[l].sum()) if not df_mes.empty else 0 for l in lineas}
        c1, c2, *cx, cn = st.columns(2 + len(lineas))
        c1.metric("Facturación total", ars(total_mes), delta_str)
        for ci, (col, lbl) in zip(cx + [cx[-1]] if cx else [c2], zip(lineas, labels)):
            ci.metric(lbl, ars(linea_vals[col]))
        cn.metric("Transacciones", num(cant_mes))
    else:
        c1, c2 = st.columns(2)
        c1.metric("Facturación total", ars(total_mes), delta_str)
        c2.metric("Transacciones",     num(cant_mes))

    st.divider()

    # ── Gráfico evolución ─────────────────────────────────────
    if tiene_lineas:
        col_a, col_b = st.columns([2, 1])
    else:
        col_a = st.container()
        col_b = None

    with col_a:
        st.markdown("##### Evolución mensual")
        df_monthly = df_v.groupby("periodo").agg(
            total=("total","sum"),
            **{l: (l,"sum") for l in lineas if l in df_v.columns}
        ).reset_index().sort_values("periodo")
        df_monthly["label"] = df_monthly["periodo"].apply(lambda p: periodo_label(p.to_timestamp()))

        fig = go.Figure()
        if tiene_lineas:
            colores_lineas = [colores["primario"], colores["secundario"],
                              "#8E44AD","#E67E22","#27AE60"]
            for i, (col, lbl) in enumerate(zip(lineas, labels)):
                fig.add_trace(go.Bar(
                    x=df_monthly["label"], y=df_monthly[col],
                    name=lbl, marker_color=colores_lineas[i % len(colores_lineas)],
                    hovertemplate=f"<b>%{{x}}</b><br>{lbl}: $%{{y:,.0f}}<extra></extra>"
                ))
            layout_extra = dict(barmode="stack")
        else:
            fig.add_trace(go.Bar(
                x=df_monthly["label"], y=df_monthly["total"],
                name="Ventas", marker_color=colores["primario"],
                hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>"
            ))
            layout_extra = {}

        fig.update_layout(
            **layout_extra,
            height=320, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Torta de mix (solo si hay líneas) ─────────────────────
    if tiene_lineas and col_b is not None:
        with col_b:
            st.markdown("##### Mix del período")
            vals = [linea_vals[l] for l in lineas]
            if sum(vals) > 0:
                fig_pie = go.Figure(go.Pie(
                    labels=labels, values=vals,
                    marker_colors=[colores["primario"], colores["secundario"],
                                   "#8E44AD","#E67E22"],
                    hole=0.45, textinfo="label+percent",
                    hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>"
                ))
                fig_pie.update_layout(
                    height=280, margin=dict(l=0,r=0,t=10,b=0),
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=False
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sin datos de líneas para este período.")

    # ── Top clientes ──────────────────────────────────────────
    if not df_mes.empty and "cliente" in df_mes.columns:
        st.markdown("##### Top clientes del período")
        top = (df_mes.groupby("cliente")["total"]
               .sum().sort_values(ascending=False).head(10).reset_index())
        top["total_fmt"] = top["total"].apply(ars)
        fig_h = go.Figure(go.Bar(
            x=top["total"], y=top["cliente"],
            orientation="h", marker_color=colores["primario"],
            text=top["total_fmt"], textposition="outside",
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>"
        ))
        fig_h.update_layout(
            height=max(250, len(top)*35),
            margin=dict(l=0,r=90,t=10,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickformat="$,.0f", gridcolor="#EEE"),
            yaxis=dict(autorange="reversed"), showlegend=False
        )
        st.plotly_chart(fig_h, use_container_width=True)

    # ── Detalle ───────────────────────────────────────────────
    with st.expander("Ver detalle de transacciones"):
        cols_show = ["fecha","cliente","cantidad"] + lineas + ["total"]
        cols_show = [c for c in cols_show if c in df_mes.columns]
        df_show = df_mes[cols_show].copy()
        df_show["fecha"] = df_show["fecha"].dt.strftime("%d/%m/%Y")
        for col in lineas + ["total"]:
            if col in df_show.columns:
                df_show[col] = df_show[col].apply(lambda x: ars(x) if pd.notna(x) else "—")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
