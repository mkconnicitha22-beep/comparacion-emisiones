from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def cargar_datos(ruta_csv: str = "data/emisiones_limpias.csv") -> pd.DataFrame:
    """
    Carga el dataset limpio del proyecto. Si aún no existe el archivo local,
    genera un dataset realista de respaldo con la estructura estándar para pruebas.
    """
    ruta = Path(ruta_csv)
    if ruta.exists():
        df = pd.read_csv(ruta)
        df.columns = [c.strip().lower() for c in df.columns]
        return df

    # Dataset de respaldo (Chile, Brasil, EE.UU., China, Alemania) 2000-2023
    np.random.seed(42)
    paises = {
        "Chile": ("América del Sur", 55.0, 1.4),
        "Brasil": ("América del Sur", 320.0, 6.5),
        "Estados Unidos": ("América del Norte", 5700.0, -38.0),
        "China": ("Asia", 3600.0, 360.0),
        "Alemania": ("Europa", 850.0, -11.0),
    }
    sectores = ["Energía", "Transporte", "Industria"]
    pesos_sector = {"Energía": 0.48, "Transporte": 0.30, "Industria": 0.22}

    registros = []
    for pais, (region, base, tendencia) in paises.items():
        for i, anio in enumerate(range(2000, 2024)):
            total_anio = max(base + tendencia * i + np.random.normal(0, base * 0.03), 10)
            for sector in sectores:
                emision = round(total_anio * pesos_sector[sector], 2)
                registros.append({
                    "pais": pais,
                    "region": region,
                    "anio": anio,
                    "sector": sector,
                    "emisiones_mtco2": emision,
                })
    return pd.DataFrame(registros)