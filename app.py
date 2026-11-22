import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.data_loader import cargar_datos
from src.models import proyectar_promedio_movil, proyectar_regresion_lineal

# 1. Configuración general de página
st.set_page_config(
    page_title="Monitor Internacional de Emisiones",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Dashboard de Comparación Internacional de Emisiones")
st.markdown(
    "Herramienta interactiva para el análisis histórico de emisiones de gases de efecto "
    "invernadero ($MtCO_2e$) y simulación de escenarios futuros mediante modelamiento matemático."
)

df = cargar_datos()

# -------------------------------------------------------------------------
# BARRA LATERAL: FILTROS INTERACTIVOS (Requerimiento >= 3 filtros)
# -------------------------------------------------------------------------
st.sidebar.header("🔎 Filtros de Exploración")

regiones_disp = sorted(df["region"].unique())
region_sel = st.sidebar.multiselect(
    "1. Región Geográfica",
    options=regiones_disp,
    default=regiones_disp,
)

paises_filtrados = sorted(df[df["region"].isin(region_sel)]["pais"].unique())
paises_sel = st.sidebar.multiselect(
    "2. Países a Analizar",
    options=paises_filtrados,
    default=paises_filtrados[:3] if len(paises_filtrados) >= 3 else paises_filtrados,
)

sectores_disp = sorted(df["sector"].unique())
sectores_sel = st.sidebar.multiselect(
    "3. Sector Emisor",
    options=sectores_disp,
    default=sectores_disp,
)

anio_min, anio_max = int(df["anio"].min()), int(df["anio"].max())
rango_anios = st.sidebar.slider(
    "4. Rango Histórico de Años",
    min_value=anio_min,
    max_value=anio_max,
    value=(anio_min, anio_max),
)

# -------------------------------------------------------------------------
# BARRA LATERAL: PARÁMETROS DEL MODELO (Requerimiento >= 2 parámetros + Extra)
# -------------------------------------------------------------------------
st.sidebar.divider()
st.sidebar.header("📈 Parámetros de Proyección")

pais_objetivo = st.sidebar.selectbox(
    "País para Proyección Individual",
    options=paises_sel if paises_sel else paises_filtrados,
)

horizonte_anios = st.sidebar.slider(
    "Horizonte de Proyección (años)",
    min_value=1,
    max_value=20,
    value=10,
)

metodo_modelo = st.sidebar.radio(
    "Modelo Matemático a Visualizar",
    options=[
        "Comparar Ambos Modelos (Desafío Extra)",
        "Regresión Lineal (OLS)",
        "Promedio Móvil",
    ],
)

ventana_pm = st.sidebar.slider(
    "Ventana del Promedio Móvil (k años)",
    min_value=2,
    max_value=10,
    value=4,
    help="Cantidad de períodos históricos recientes usados para calcular el promedio móvil.",
)

# Validación de selección
if not paises_sel or not sectores_sel:
    st.warning("⚠️ Selecciona al menos un país y un sector en la barra lateral para visualizar datos.")
    st.stop()

# Filtrado del DataFrame
df_filtrado = df[
    (df["region"].isin(region_sel))
    & (df["pais"].isin(paises_sel))
    & (df["sector"].isin(sectores_sel))
    & (df["anio"].between(rango_anios[0], rango_anios[1]))
]

# -------------------------------------------------------------------------
# SECCIÓN A: INDICADORES DINÁMICOS AUTOMÁTICOS (Requerimiento >= 3 KPIs)
# -------------------------------------------------------------------------
st.subheader("📊 Indicadores Clave del Período Seleccionado")

serie_anual_total = df_filtrado.groupby("anio")["emisiones_mtco2"].sum().reset_index()

total_acumulado = df_filtrado["emisiones_mtco2"].sum()
promedio_anual = serie_anual_total["emisiones_mtco2"].mean()
maximo_anual = serie_anual_total["emisiones_mtco2"].max()
anio_pico = int(serie_anual_total.loc[serie_anual_total["emisiones_mtco2"].idxmax(), "anio"])

if len(serie_anual_total) >= 2:
    val_inicio = serie_anual_total.iloc[0]["emisiones_mtco2"]
    val_fin = serie_anual_total.iloc[-1]["emisiones_mtco2"]
    variacion_pct = ((val_fin - val_inicio) / val_inicio) * 100 if val_inicio != 0 else 0.0
else:
    variacion_pct = 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Acumulado", f"{total_acumulado:,.1f} MtCO₂")
col2.metric("Promedio Anual", f"{promedio_anual:,.1f} MtCO₂/año")
col3.metric(f"Máximo Histórico ({anio_pico})", f"{maximo_anual:,.1f} MtCO₂")
col4.metric(
    "Variación Período",
    f"{variacion_pct:+.1f}%",
    delta=f"{variacion_pct:+.1f}% vs año inicial",
    delta_color="inverse",
)

# -------------------------------------------------------------------------
# SECCIÓN B: EXPLORACIÓN HISTÓRICA (Gráfico 1)
# -------------------------------------------------------------------------
st.divider()
st.subheader("📉 Evolución Histórica y Comparación Internacional")

tab1, tab2 = st.tabs(["Tendencia por País", "Distribución por Sector"])

with tab1:
    df_pais_anio = (
        df_filtrado.groupby(["anio", "pais"], as_index=False)["emisiones_mtco2"].sum()
    )
    fig_hist = px.line(
        df_pais_anio,
        x="anio",
        y="emisiones_mtco2",
        color="pais",
        markers=True,
        labels={"anio": "Año", "emisiones_mtco2": "Emisiones (MtCO₂)", "pais": "País"},
        title=f"Trayectoria Histórica de Emisiones ({rango_anios[0]} - {rango_anios[1]})",
    )
    fig_hist.update_layout(hovermode="x unified")
    st.plotly_chart(fig_hist, use_container_width=True)

with tab2:
    df_sector = (
        df_filtrado.groupby(["pais", "sector"], as_index=False)["emisiones_mtco2"].sum()
    )
    fig_bar = px.bar(
        df_sector,
        x="pais",
        y="emisiones_mtco2",
        color="sector",
        barmode="stack",
        labels={"pais": "País", "emisiones_mtco2": "Emisiones Acumuladas (MtCO₂)", "sector": "Sector"},
        title="Composición Sectorial Acumulada por País",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------------------------------------------------
# SECCIÓN C: PROYECCIÓN MATEMÁTICA Y COMPARACIÓN DE MODELOS (Gráfico 2)
# -------------------------------------------------------------------------
st.divider()
st.subheader(f"🔮 Proyección Matemática de Escenarios: {pais_objetivo}")

df_obj = (
    df_filtrado[df_filtrado["pais"] == pais_objetivo]
    .groupby("anio", as_index=False)["emisiones_mtco2"]
    .sum()
    .rename(columns={"emisiones_mtco2": "valor"})
    .sort_values("anio")
)

if len(df_obj) < 3:
    st.error("Se requieren al menos 3 años de datos históricos para generar una proyección confiable.")
else:
    df_rl = proyectar_regresion_lineal(df_obj, horizonte_anios)
    df_pm = proyectar_promedio_movil(df_obj, horizonte_anios, ventana=ventana_pm)

    fig_proy = go.Figure()

    # Serie histórica
    fig_proy.add_trace(
        go.Scatter(
            x=df_obj["anio"],
            y=df_obj["valor"],
            mode="lines+markers",
            name="Datos Históricos",
            line=dict(color="#1f77b4", width=3),
        )
    )

    # Punto de unión para continuidad visual
    ultimo_hist = df_obj.iloc[-1:]

    if metodo_modelo in ["Regresión Lineal (OLS)", "Comparar Ambos Modelos (Desafío Extra)"]:
        df_rl_plot = pd.concat([ultimo_hist[["anio", "valor"]], df_rl[["anio", "valor"]]])
        fig_proy.add_trace(
            go.Scatter(
                x=df_rl_plot["anio"],
                y=df_rl_plot["valor"],
                mode="lines+markers",
                name="Proyección: Regresión Lineal",
                line=dict(color="#d62728", width=3, dash="dash"),
            )
        )

    if metodo_modelo in ["Promedio Móvil", "Comparar Ambos Modelos (Desafío Extra)"]:
        df_pm_plot = pd.concat([ultimo_hist[["anio", "valor"]], df_pm[["anio", "valor"]]])
        fig_proy.add_trace(
            go.Scatter(
                x=df_pm_plot["anio"],
                y=df_pm_plot["valor"],
                mode="lines+markers",
                name=f"Proyección: Promedio Móvil (k={ventana_pm})",
                line=dict(color="#2ca02c", width=3, dash="dot"),
            )
        )

    fig_proy.update_layout(
        title=f"Escenarios Proyectados a {horizonte_anios} Años para {pais_objetivo}",
        xaxis_title="Año",
        yaxis_title="Emisiones Proyectadas (MtCO₂)",
        hovermode="x unified",
    )
    st.plotly_chart(fig_proy, use_container_width=True)

    # Métricas comparativas de cierre de horizonte
    anio_final_proy = int(df_rl["anio"].max())
    val_actual = float(df_obj.iloc[-1]["valor"])
    val_rl_fin = float(df_rl.iloc[-1]["valor"])
    val_pm_fin = float(df_pm.iloc[-1]["valor"])
    r2_modelo = float(df_rl["r2"].iloc[0])
    pendiente_anual = float(df_rl["pendiente"].iloc[0])

    c1, c2, c3 = st.columns(3)
    c1.metric(
        f"Escenario Lineal ({anio_final_proy})",
        f"{val_rl_fin:,.1f} MtCO₂",
        delta=f"{val_rl_fin - val_actual:+.1f} MtCO₂ vs {int(df_obj['anio'].max())}",
        delta_color="inverse",
    )
    c2.metric(
        f"Escenario Promedio Móvil ({anio_final_proy})",
        f"{val_pm_fin:,.1f} MtCO₂",
        delta=f"{val_pm_fin - val_actual:+.1f} MtCO₂ vs {int(df_obj['anio'].max())}",
        delta_color="inverse",
    )
    c3.metric(
        "Ajuste Lineal ($R^2$) / Pendiente",
        f"R² = {r2_modelo:.3f}",
        delta=f"{pendiente_anual:+.2f} MtCO₂ / año",
        delta_color="off",
    )

    with st.expander("📋 Ver Tabla de Datos Proyectados"):
        tabla_comp = pd.DataFrame({
            "Año": df_rl["anio"],
            "Regresión Lineal (MtCO₂)": df_rl["valor"].round(2),
            f"Promedio Móvil k={ventana_pm} (MtCO₂)": df_pm["valor"].round(2),
            "Brecha entre Modelos (MtCO₂)": (df_rl["valor"] - df_pm["valor"]).round(2),
        })
        st.dataframe(tabla_comp, use_container_width=True, hide_index=True)