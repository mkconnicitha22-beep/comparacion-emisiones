import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def proyectar_regresion_lineal(df_serie: pd.DataFrame, anios_proyectar: int) -> pd.DataFrame:
    """
    Ajusta una Regresión Lineal Ordinaria (OLS) sobre la serie histórica
    y proyecta N años hacia el futuro.
    """
    X = df_serie[["anio"]].values
    y = df_serie["valor"].values

    modelo = LinearRegression()
    modelo.fit(X, y)

    ultimo_anio = int(df_serie["anio"].max())
    anios_futuros = np.arange(ultimo_anio + 1, ultimo_anio + anios_proyectar + 1).reshape(-1, 1)
    predicciones = modelo.predict(anios_futuros)

    # Evitar emisiones físicamente imposibles (negativas)
    predicciones = np.maximum(predicciones, 0)

    r2 = modelo.score(X, y)
    pendiente = float(modelo.coef_[0])

    df_futuro = pd.DataFrame({
        "anio": anios_futuros.flatten(),
        "valor": predicciones,
        "tipo": "Proyección: Regresión Lineal",
        "r2": r2,
        "pendiente": pendiente
    })
    return df_futuro


def proyectar_promedio_movil(
    df_serie: pd.DataFrame, anios_proyectar: int, ventana: int = 3
) -> pd.DataFrame:
    """
    Proyecta de forma iterativa utilizando el promedio móvil de los últimos k períodos.
    """
    historial = list(df_serie["valor"].values)
    ultimo_anio = int(df_serie["anio"].max())
    ventana_real = min(ventana, len(historial))

    predicciones = []
    anios_futuros = []

    for i in range(1, anios_proyectar + 1):
        # Promedio de los últimos k valores (incluyendo predicciones previas)
        siguiente_valor = float(np.mean(historial[-ventana_real:]))
        predicciones.append(max(siguiente_valor, 0.0))
        anios_futuros.append(ultimo_anio + i)
        historial.append(siguiente_valor)

    return pd.DataFrame({
        "anio": anios_futuros,
        "valor": predicciones,
        "tipo": f"Proyección: Promedio Móvil (k={ventana_real})"
    })
    