"""Módulo completo para análisis de datos reales de F1
con interfaz limpia y funcional"""

import streamlit as st
import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import logging
import os

# Configuración de inicio

st.set_page_config(
    page_title="F1 Analytics Pro",
    page_icon="🏎️",
    layout="centered"
)

st.markdown("<h1 style='color:#3b82f6;text-align:center;'>🏎️ F1 Analytics Pro</h1>", unsafe_allow_html=True)
st.divider()

# Desactivar logs de FastF1
logging.getLogger('fastf1').setLevel(logging.CRITICAL)

# Habilitar cache (para crear carpeta si no existe)
cache_dir = './data/raw/cache'
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# Sidebar - para programar las configuraciones

st.sidebar.markdown("### ⚙️ Configuración")

# Año
year = st.sidebar.slider("📅 Año:", min_value=2018, max_value=2024, value=2024)

# Gran Premio
gp_list = [
    'Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China',
    'Monaco', 'Canada', 'Spain', 'Austria', 'Silverstone',
    'Hungary', 'Belgium', 'Netherlands', 'Monza', 'Singapore',
    'Mexico', 'Brazil', 'Las Vegas', 'Abu Dhabi'
]
gp = st.sidebar.selectbox("🏁 Gran Premio:", gp_list, index=13)

st.sidebar.divider()

# Botones
load_btn = st.sidebar.button("🔥 Cargar Datos", use_container_width=True)
clear_btn = st.sidebar.button("🔄 Limpiar", use_container_width=True)

# Inicializar sesión
if 'session' not in st.session_state:
    st.session_state.session = None

if clear_btn:
    st.session_state.session = None
    st.rerun()

# Cargando datos - mientras se procesa

if load_btn:
    with st.spinner(f"⏳ Cargando {gp} {year}..."):
        try:
            session = fastf1.get_session(year, gp, 'R')
            session.load()
            st.session_state.session = session
            st.success(f"✅ Cargado: {gp} {year}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state.session = None

# Análisis

if st.session_state.session is not None:
    session = st.session_state.session
    
    # Información básica
    st.markdown("### 📊 Información de la Carrera")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏁 Carrera", session.event['EventName'])
    with col2:
        st.metric("📅 Fecha", str(session.event['EventDate']).split()[0])
    with col3:
        st.metric("👥 Pilotos", len(session.drivers))
    with col4:
        st.metric("📍 País", session.event['Country'])
    
    st.divider()
    
    # Tablas de Análisis
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Resultados", "⏱️ Análisis por Piloto", "🛞 Neumáticos", "📈 Comparación"])
    
    # Tabla 1-Resultados
    with tab1:
        st.markdown("### 🏆 Clasificación Final")
        
        # Obtener resultados
        results = session.results[['Position', 'Abbreviation', 'TeamName', 'Points', 'Status']]
        results = results.sort_values('Position').reset_index(drop=True)
        results.columns = ['Posición', 'Piloto', 'Equipo', 'Puntos', 'Estado']
        
        # Mostrar tabla
        st.dataframe(results.head(15), use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Podio
        st.markdown("### 🎖️ Podio")
        podio_col1, podio_col2, podio_col3 = st.columns(3)
        
        podio = results.head(3)
        medallas = ['🥇 1º', '🥈 2º', '🥉 3º']
        cols = [podio_col1, podio_col2, podio_col3]
        
        for i, (idx, row) in enumerate(podio.iterrows()):
            with cols[i]:
                st.info(f"**{medallas[i]}**\n\n**{row['Piloto']}**\n\n{row['Equipo']}\n\n{int(row['Puntos'])} pts")
        
        st.divider()
        
        # Gráfico de puntos
        st.markdown("### 📊 Puntos Top 10")
        top10 = results.head(10)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32' if i == 2 else '#3b82f6' for i in range(len(top10))]
        ax.barh(top10['Piloto'], top10['Puntos'].astype(float), color=colors, edgecolor='black')
        ax.set_xlabel('Puntos')
        ax.set_title('Clasificación Top 10')
        ax.grid(axis='x', alpha=0.3)
        st.pyplot(fig)
    
    # Tabla 2-Análisis por piloto
    with tab2:
        st.markdown("### ⏱️ Análisis de Tiempos por Piloto")
        
        # Seleccionar piloto
        drivers = results['Piloto'].tolist()
        selected_driver = st.selectbox("Selecciona un piloto:", drivers)
        
        # Obtener vueltas del piloto
        laps = session.laps.pick_driver(selected_driver)
        laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
        laps_clean = laps[laps['LapTimeSeconds'].notna()]
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔢 Vueltas", len(laps_clean))
        with col2:
            st.metric("⚡ Más Rápida", f"{laps_clean['LapTimeSeconds'].min():.2f}s")
        with col3:
            st.metric("🐌 Más Lenta", f"{laps_clean['LapTimeSeconds'].max():.2f}s")
        with col4:
            st.metric("📊 Promedio", f"{laps_clean['LapTimeSeconds'].mean():.2f}s")
        
        st.divider()
        
        # Gráfico de tiempos por vuelta
        st.markdown("### 📈 Tiempos por Vuelta")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(laps_clean['LapNumber'], laps_clean['LapTimeSeconds'], 
                marker='o', linewidth=2, color='#3b82f6', markersize=4)
        ax.axhline(y=laps_clean['LapTimeSeconds'].mean(), 
                   color='#f59e0b', linestyle='--', label='Promedio', linewidth=2)
        ax.set_xlabel('Número de Vuelta')
        ax.set_ylabel('Tiempo (segundos)')
        ax.set_title(f'Ritmo de Carrera - {selected_driver}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        st.divider()
        
        # Tabla de vueltas
        st.markdown("### 📋 Detalle de Vueltas (Top 20)")
        laps_display = laps_clean[['LapNumber', 'LapTimeSeconds', 'Compound', 'TyreLife']].head(20)
        laps_display.columns = ['Vuelta', 'Tiempo (s)', 'Neumático', 'Vida del Neumático']
        st.dataframe(laps_display, use_container_width=True, hide_index=True)
    
    # Tabla 3-Análisis neumáticos
    with tab3:
        st.markdown("### 🛞 Análisis de Neumáticos y Estrategia")
        
        # Seleccionar piloto
        selected_driver_tyre = st.selectbox("Selecciona un piloto:", drivers, key="tyre_driver")
        
        # Obtener vueltas del piloto
        laps_tyre = session.laps.pick_driver(selected_driver_tyre)
        laps_tyre['LapTimeSeconds'] = laps_tyre['LapTime'].dt.total_seconds()
        laps_tyre_clean = laps_tyre[laps_tyre['LapTimeSeconds'].notna()]
        
        st.markdown(f"**Vueltas totales registradas:** {len(laps_tyre_clean)}")
        
        st.divider()
        
        # Gráfico de ritmo por vuelta coloreado por neumático
        st.markdown("### 📊 Ritmo por Vuelta (coloreado por neumático)")
        
        fig, ax = plt.subplots(figsize=(12, 5))
        
        # Colores por compuesto
        compound_colors = {
            'SOFT': '#FF0000',
            'MEDIUM': '#FFA500',
            'HARD': '#FFFFFF',
            'INTERMEDIATE': '#00FF00',
            'WET': '#0000FF'
        }
        
        for compound in laps_tyre_clean['Compound'].unique():
            compound_laps = laps_tyre_clean[laps_tyre_clean['Compound'] == compound]
            color = compound_colors.get(compound, '#3b82f6')
            ax.plot(compound_laps['LapNumber'], compound_laps['LapTimeSeconds'],
                   marker='o', linewidth=2, markersize=5, label=compound, color=color)
        
        ax.set_xlabel('Número de Vuelta')
        ax.set_ylabel('Tiempo (segundos)')
        ax.set_title(f'Ritmo de Carrera por Neumático - {selected_driver_tyre}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        st.divider()
        
        # Estadísticas por neumático
        st.markdown("### 📈 Estadísticas por Tipo de Neumático")
        
        tyre_stats = []
        for compound in laps_tyre_clean['Compound'].unique():
            compound_laps = laps_tyre_clean[laps_tyre_clean['Compound'] == compound]
            tyre_stats.append({
                'Neumático': compound,
                'Vueltas': len(compound_laps),
                'Tiempo Promedio': f"{compound_laps['LapTimeSeconds'].mean():.2f}s",
                'Más Rápida': f"{compound_laps['LapTimeSeconds'].min():.2f}s",
                'Más Lenta': f"{compound_laps['LapTimeSeconds'].max():.2f}s"
            })
        
        tyre_stats_df = pd.DataFrame(tyre_stats)
        st.dataframe(tyre_stats_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Recomendación
        if len(tyre_stats) > 0:
            avg_times = {stat['Neumático']: float(stat['Tiempo Promedio'].replace('s', '')) for stat in tyre_stats}
            best_tyre = min(avg_times, key=avg_times.get)
            st.success(f"💡 **Mejor rendimiento promedio:** {best_tyre} con {avg_times[best_tyre]:.2f}s por vuelta")
        
        # Tabla detallada de neumáticos
        st.markdown("### 🛞 Detalle de Neumáticos por Vuelta")
        tyre_detail = laps_tyre_clean[['LapNumber', 'Compound', 'TyreLife', 'LapTimeSeconds']].copy()
        tyre_detail.columns = ['Vuelta', 'Neumático', 'Vida', 'Tiempo (s)']
        tyre_detail['Tiempo (s)'] = tyre_detail['Tiempo (s)'].round(3)
        st.dataframe(tyre_detail.head(20), use_container_width=True, hide_index=True)
    
    # Tabla 4-Comparación pilotos
    with tab4:
        st.markdown("### 📈 Comparación entre Pilotos")
        
        # Seleccionar pilotos para comparar
        drivers = results['Piloto'].tolist()
        selected_drivers = st.multiselect(
            "Selecciona pilotos (máximo 5):",
            drivers,
            default=drivers[:3] if len(drivers) >= 3 else drivers,
            max_selections=5
        )
        
        if len(selected_drivers) >= 2:
            # Gráfico comparativo
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for driver in selected_drivers:
                driver_laps = session.laps.pick_driver(driver)
                driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
                driver_laps_clean = driver_laps[driver_laps['LapTimeSeconds'].notna()]
                
                ax.plot(driver_laps_clean['LapNumber'], driver_laps_clean['LapTimeSeconds'],
                       marker='o', linewidth=2, markersize=4, label=driver, alpha=0.8)
            
            ax.set_xlabel('Número de Vuelta')
            ax.set_ylabel('Tiempo (segundos)')
            ax.set_title('Comparación de Ritmo de Carrera')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            
            st.divider()
            
            # Estadísticas comparativas
            st.markdown("### 📊 Estadísticas Comparativas")
            
            stats_data = []
            for driver in selected_drivers:
                driver_laps = session.laps.pick_driver(driver)
                driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
                driver_laps_clean = driver_laps[driver_laps['LapTimeSeconds'].notna()]
                
                stats_data.append({
                    'Piloto': driver,
                    'Vueltas': len(driver_laps_clean),
                    'Más Rápida': f"{driver_laps_clean['LapTimeSeconds'].min():.2f}s",
                    'Promedio': f"{driver_laps_clean['LapTimeSeconds'].mean():.2f}s",
                    'Más Lenta': f"{driver_laps_clean['LapTimeSeconds'].max():.2f}s"
                })
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        else:
            st.warning("⚠️ Selecciona al menos 2 pilotos para comparar")

else:
    # Mensaje inicial
    st.info("👈 Usa el panel lateral para seleccionar un año y Gran Premio, luego haz clic en 'Cargar Datos'")
    st.markdown("""
    ### ℹ️ Sobre este módulo
    
    **F1 Analytics Pro** te permite:
    - 🏆 Ver resultados y clasificaciones finales
    - ⏱️ Analizar tiempos de vuelta por piloto
    - 🛞 Analizar estrategias de neumáticos y degradación
    - 📈 Comparar rendimiento entre pilotos
    - 📊 Visualizar estadísticas detalladas de carrera
    
    Datos proporcionados por **FastF1** (datos oficiales de F1)
    """)

st.divider()
st.markdown("<small style='color:#94a3b8;'>Proyecto Final - Ingeniería Aeroespacial (UDEA, 2025)</small>", unsafe_allow_html=True)