"""
ANÁLISIS DE CARRERAS REALES DE FÓRMULA 1
----------------------------------------
Este módulo usa FastF1 para cargar datos reales de la F1:
- Mostrar pilotos, vueltas, neumáticos usados y tiempos.
- Graficar el ritmo por vuelta o velocidad promedio.
"""

import streamlit as st
import fastf1
import fastf1.plotting
from matplotlib import pyplot as plt
import pandas as pd

# =========================
# CONFIGURACIÓN INICIAL
# =========================
st.set_page_config(page_title="Análisis F1 Real", page_icon="📊", layout="centered")
st.markdown("<h1 style='color:#3b82f6;text-align:center;'>📊 Análisis Real de Carreras F1</h1>", unsafe_allow_html=True)
st.divider()

# Activa la caché de FastF1 (acelera cargas futuras)
fastf1.Cache.enable_cache("fastf1_cache")

# =========================
# SELECCIÓN DE TEMPORADA Y GRAN PREMIO
# =========================
st.markdown("### Selecciona la carrera que quieres analizar")

year = st.selectbox("Temporada", [2021, 2022, 2023, 2024])
gp = st.text_input("Gran Premio (ejemplo: Monaco, Monza, Silverstone, Brazil, Spain):", "Monaco")

if st.button("🔍 Cargar datos reales"):
    with st.spinner("Descargando datos reales... (puede tardar 10-20 seg)"):
        try:
            # Cargar la sesión de carrera
            session = fastf1.get_session(year, gp, 'R')
            session.load()

            st.success(f"✅ Datos cargados: {session.event['EventName']} - {year}")
            st.markdown(f"**Fecha:** {session.event['EventDate']}  |  **Vueltas:** {len(session.laps)}")

            # Lista de pilotos
            drivers = session.drivers
            driver_names = [session.get_driver(i)['Abbreviation'] for i in drivers]
            driver_selected = st.selectbox("Selecciona un piloto", driver_names)

            laps = session.laps.pick_driver(driver_selected)
            st.write(f"Vueltas registradas de {driver_selected}: {len(laps)}")

            # =========================
            # GRÁFICO DE RITMO POR VUELTA
            # =========================
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(laps['LapNumber'], laps['LapTime'].dt.total_seconds(), color='#3b82f6', marker='o', linewidth=1)
            ax.set_title(f"Tiempos por vuelta - {driver_selected} ({gp} {year})")
            ax.set_xlabel("Número de vuelta")
            ax.set_ylabel("Tiempo (segundos)")
            ax.grid(True)
            st.pyplot(fig)

            # =========================
            # TABLA DE NEUMÁTICOS
            # =========================
            st.markdown("### 🛞 Neumáticos usados")
            tyre_stints = laps[['LapNumber', 'Compound', 'TyreLife', 'LapTime']].copy()
            tyre_stints['LapTime'] = tyre_stints['LapTime'].dt.total_seconds().round(3)
            st.dataframe(tyre_stints.head(20))

            # =========================
            # ANÁLISIS DE PROMEDIO
            # =========================
            avg_time = tyre_stints['LapTime'].mean()
            st.info(f"⏱️ Promedio de vuelta: **{avg_time:.2f} s**")

            # Recomendación basada en rendimiento
            best_tyre = tyre_stints.groupby("Compound")["LapTime"].mean().idxmin()
            st.success(f"💡 Mejor rendimiento con neumático **{best_tyre}** en esta carrera.")

        except Exception as e:
            st.error(f"⚠️ Error al cargar datos: {e}")

st.divider()
st.markdown("<small style='color:#94a3b8;'>Proyecto Final - Ingeniería Aeroespacial (Programación y ciencia computacional 2025-2)</small>", unsafe_allow_html=True)
