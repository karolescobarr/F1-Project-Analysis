import streamlit as st
import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# =====================================================================
# CONFIGURACIÓN OFICIAL F1
# =====================================================================

st.set_page_config(
    page_title="F1 Analysis Pro",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colores oficiales F1
F1_RED = "#E10600"
F1_WHITE = "#FFFFFF"
F1_BLACK = "#000000"
F1_GRAY = "#333333"
F1_GOLD = "#FFD700"

# Desactivar logs
logging.getLogger('fastf1').setLevel(logging.CRITICAL)

# Habilitar cache (crear carpeta si no existe)
import os
cache_dir = './data/raw/cache'
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# =====================================================================
# ESTILOS OFICIALES F1
# =====================================================================

st.markdown(f"""
    <style>
        * {{
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif;
        }}
        
        .main {{
            background: linear-gradient(180deg, {F1_BLACK} 0%, #1a1a1a 100%);
            color: {F1_WHITE};
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {F1_GRAY};
            border-bottom: 4px solid {F1_RED};
            gap: 0;
        }}
        
        .stTabs [aria-selected="true"] {{
            color: {F1_RED} !important;
            background-color: {F1_BLACK} !important;
            border-bottom: 4px solid {F1_RED} !important;
            font-weight: bold;
        }}
        
        h1 {{
            color: {F1_RED};
            font-size: 3.5em;
            font-weight: 900;
            text-shadow: 0 2px 10px rgba(225, 6, 0, 0.4);
            letter-spacing: 2px;
        }}
        
        h2 {{
            color: {F1_RED};
            font-size: 2em;
            margin-top: 20px;
            font-weight: 800;
        }}
        
        h3 {{
            color: {F1_GOLD};
            font-size: 1.5em;
            font-weight: 700;
        }}
        
        .header-official {{
            background: linear-gradient(90deg, {F1_BLACK}, {F1_GRAY}, {F1_BLACK});
            padding: 30px;
            border-top: 5px solid {F1_RED};
            border-bottom: 5px solid {F1_RED};
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .race-info-card {{
            background: linear-gradient(135deg, {F1_GRAY}, #1a1a1a);
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid {F1_RED};
            box-shadow: 0 4px 15px rgba(225, 6, 0, 0.2);
            margin: 10px 0;
        }}
        
        .podium-card {{
            background: linear-gradient(135deg, {F1_RED}, #990400);
            padding: 20px;
            border-radius: 10px;
            color: {F1_WHITE};
            text-align: center;
            box-shadow: 0 6px 20px rgba(225, 6, 0, 0.3);
            margin: 10px 0;
        }}
        
        .link-button {{
            display: inline-block;
            background-color: {F1_RED};
            color: {F1_WHITE};
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            margin: 5px;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        .link-button:hover {{
            background-color: #CC0500;
            transform: scale(1.05);
        }}
        
        button {{
            background-color: {F1_RED} !important;
            color: {F1_WHITE} !important;
            font-weight: bold !important;
            border-radius: 5px !important;
            border: none !important;
            padding: 12px 24px !important;
            font-size: 1em !important;
            transition: all 0.3s ease !important;
        }}
        
        button:hover {{
            background-color: #CC0500 !important;
            box-shadow: 0 0 30px rgba(225, 6, 0, 0.6) !important;
            transform: translateY(-2px) !important;
        }}
        
        .sidebar {{
            background: linear-gradient(180deg, {F1_BLACK}, {F1_GRAY});
        }}
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# HEADER OFICIAL
# =====================================================================

st.markdown(f"""
    <div class='header-official'>
        <div style='font-size: 3.5em; font-weight: 900; color: {F1_RED}; letter-spacing: 3px;'>
            🏁 FORMULA 1 ANALYTICS 🏁
        </div>
        <div style='font-size: 1.2em; color: {F1_GOLD}; margin-top: 10px; font-weight: bold;'>
            PROFESSIONAL DATA ANALYSIS & STATISTICS
        </div>
        <div style='font-size: 0.95em; color: #999; margin-top: 8px;'>
            From the Track to the Code | Real-time Race Analytics
        </div>
    </div>
""", unsafe_allow_html=True)

# =====================================================================
# SIDEBAR
# =====================================================================

st.sidebar.markdown(f"""
    <div style='text-align: center; padding: 20px; border-bottom: 3px solid {F1_RED};'>
        <h2 style='color: {F1_RED}; margin: 0;'>⚙️ CONFIGURACIÓN</h2>
    </div>
""", unsafe_allow_html=True)

# Años disponibles
años_disponibles = list(range(2018, 2025))
year = st.sidebar.select_slider(
    "📅 **Selecciona el año:**",
    options=años_disponibles,
    value=2024
)

# Mapeo de Grand Prix por año (simplificado, los principales)
gp_list = [
    'Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China',
    'Monaco', 'Canada', 'Spain', 'Austria', 'Silverstone',
    'Hungary', 'Belgium', 'Netherlands', 'Monza', 'Singapore',
    'Mexico', 'Brazil', 'Las Vegas', 'Abu Dhabi'
]

gp = st.sidebar.selectbox(
    "🏁 **Gran Premio:**",
    gp_list,
    index=13
)

st.sidebar.markdown("---")

# Opciones avanzadas
st.sidebar.markdown("**🔧 OPCIONES AVANZADAS**")
show_details = st.sidebar.checkbox("Detalles Completos", value=True)
show_links = st.sidebar.checkbox("Enlaces Oficiales", value=True)

st.sidebar.markdown("---")

# Botones
col_btn1, col_btn2 = st.sidebar.columns([1, 1])

with col_btn1:
    load_btn = st.button("📥 CARGAR", use_container_width=True, key="load")

with col_btn2:
    clear_btn = st.button("🔄 LIMPIAR", use_container_width=True, key="clear")

# Inicializar sesión
if 'loading' not in st.session_state:
    st.session_state.loading = False

if load_btn:
    st.session_state.loading = True

if clear_btn:
    if 'session' in st.session_state:
        del st.session_state.session
    st.rerun()

# =====================================================================
# CARGAR DATOS
# =====================================================================

if st.session_state.loading:
    progress = st.progress(0)
    status = st.empty()
    
    try:
        status.text("⏳ Conectando con FastF1...")
        progress.progress(25)
        
        session = fastf1.get_session(year, gp, 'R')
        progress.progress(50)
        
        status.text("📊 Descargando telemetría...")
        session.load()
        progress.progress(75)
        
        st.session_state.session = session
        st.session_state.loading = False
        
        progress.progress(100)
        status.text("✅ LISTO")
        
        st.success(f"✓ {gp} {year} - {len(session.drivers)} Pilotos")
        
    except Exception as e:
        st.error(f"✗ Error: {str(e)}")
        st.session_state.loading = False

# =====================================================================
# PANEL PRINCIPAL
# =====================================================================

if 'session' in st.session_state:
    session = st.session_state.session
    
    # INFO DE CARRERA
    st.markdown(f"### 🏎️ INFORMACIÓN DE LA CARRERA")
    
    info1, info2, info3, info4, info5 = st.columns(5)
    
    with info1:
        st.markdown(f"""
        <div class='race-info-card'>
            <div style='font-size: 0.85em; color: #999;'>CARRERA</div>
            <div style='font-size: 1.4em; color: {F1_RED}; font-weight: bold;'>{session.event['EventName']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with info2:
        st.markdown(f"""
        <div class='race-info-card'>
            <div style='font-size: 0.85em; color: #999;'>FECHA</div>
            <div style='font-size: 1.4em; color: {F1_GOLD}; font-weight: bold;'>{str(session.event['EventDate']).split()[0]}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with info3:
        st.markdown(f"""
        <div class='race-info-card'>
            <div style='font-size: 0.85em; color: #999;'>PILOTOS</div>
            <div style='font-size: 1.4em; color: {F1_RED}; font-weight: bold;'>{len(session.drivers)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with info4:
        st.markdown(f"""
        <div class='race-info-card'>
            <div style='font-size: 0.85em; color: #999;'>CIRCUITO</div>
            <div style='font-size: 1.2em; color: {F1_GOLD}; font-weight: bold;'>{session.event['Location']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with info5:
        st.markdown(f"""
        <div class='race-info-card'>
            <div style='font-size: 0.85em; color: #999;'>PAÍS</div>
            <div style='font-size: 1.2em; color: {F1_RED}; font-weight: bold;'>{session.event['Country']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Enlaces oficiales
    if show_links:
        st.markdown("---")
        st.markdown("### 🔗 ENLACES OFICIALES")
        
        link_col1, link_col2, link_col3, link_col4 = st.columns(4)
        
        with link_col1:
            st.markdown(f"""
            <a href='https://www.formula1.com' target='_blank' class='link-button'>🏁 F1.COM</a>
            """, unsafe_allow_html=True)
        
        with link_col2:
            st.markdown(f"""
            <a href='https://en.wikipedia.org/wiki/Formula_One' target='_blank' class='link-button'>📚 WIKIPEDIA</a>
            """, unsafe_allow_html=True)
        
        with link_col3:
            st.markdown(f"""
            <a href='https://www.youtube.com/c/Formula1' target='_blank' class='link-button'>▶️ YOUTUBE</a>
            """, unsafe_allow_html=True)
        
        with link_col4:
            st.markdown(f"""
            <a href='https://twitter.com/F1' target='_blank' class='link-button'>𝕏 OFICIAL</a>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 RESULTADOS",
        "⏱️ TIEMPOS",
        "📊 TOP 3",
        "📈 ESTADÍSTICAS",
        "🔍 ANÁLISIS"
    ])
    
    # ========== TAB 1: RESULTADOS ==========
    with tab1:
        st.markdown("### 🏆 RESULTADOS FINALES")
        
        resultados = session.results[['Position', 'Abbreviation', 'TeamName', 'Points', 'Status']]
        resultados = resultados.sort_values('Position')
        resultados.columns = ['POS', 'PILOTO', 'EQUIPO', 'PUNTOS', 'ESTADO']
        
        res_col1, res_col2 = st.columns([2, 1])
        
        with res_col1:
            st.dataframe(resultados.head(15), use_container_width=True, hide_index=True, height=600)
        
        with res_col2:
            ganador = resultados.iloc[0]
            
            st.markdown(f"""
            <div class='podium-card'>
                <div style='font-size: 0.9em;'>🥇 GANADOR</div>
                <div style='font-size: 2.5em; margin: 15px 0; font-weight: 900;'>{ganador['PILOTO']}</div>
                <div style='font-size: 1em; border-top: 2px solid white; padding-top: 10px; margin-top: 10px;'>
                    <div>{ganador['EQUIPO']}</div>
                    <div style='font-size: 1.5em; margin-top: 5px;'>{int(ganador['PUNTOS'])} PTS</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # PODIO
            podio = resultados.head(3)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight: bold; color: {F1_GOLD}; font-size: 1.2em; text-align: center;'>🎖️ PODIO</div>", unsafe_allow_html=True)
            
            medallas = ['🥇', '🥈', '🥉']
            for idx, (_, row) in enumerate(podio.iterrows()):
                st.markdown(f"<div style='text-align: center; padding: 8px; background: {F1_GRAY}; margin: 5px 0; border-radius: 5px; color: {F1_WHITE};'><strong>{medallas[idx]} {row['PILOTO']}</strong><br>{int(row['PUNTOS'])} pts</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📊 PUNTUACIÓN TOP 10")
        
        top10 = resultados.head(10)
        
        fig = go.Figure()
        colores = ['#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32' if i == 2 else '#E10600' for i in range(len(top10))]
        
        fig.add_trace(go.Bar(
            x=top10['PUNTOS'].astype(float),
            y=top10['PILOTO'],
            orientation='h',
            marker=dict(color=colores, line=dict(color='white', width=2)),
            text=top10['PUNTOS'].astype(int),
            textposition='auto'
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=500,
            showlegend=False,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#000000',
            font=dict(color='white', size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== TAB 2: TIEMPOS ==========
    with tab2:
        st.markdown("### ⏱️ TIEMPOS DE VUELTA")
        
        piloto = st.selectbox("Selecciona Piloto:", resultados['PILOTO'].tolist(), key="pilot")
        
        laps = session.laps.pick_driver(piloto)
        laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 VUELTAS", len(laps))
        with col2:
            st.metric("⚡ RÁPIDA", f"{laps['LapTimeSeconds'].min():.2f}s")
        with col3:
            st.metric("🐌 LENTA", f"{laps['LapTimeSeconds'].max():.2f}s")
        with col4:
            st.metric("📈 PROMEDIO", f"{laps['LapTimeSeconds'].mean():.2f}s")
        
        st.markdown("---")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=laps['LapNumber'],
            y=laps['LapTimeSeconds'],
            mode='lines+markers',
            name=piloto,
            line=dict(color=F1_RED, width=3),
            marker=dict(size=6, color=F1_RED, line=dict(color='white', width=1))
        ))
        
        media = laps['LapTimeSeconds'].mean()
        fig.add_hline(y=media, line_dash="dash", line_color=F1_GOLD)
        
        fig.update_layout(
            template='plotly_dark',
            height=500,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#000000',
            font=dict(color='white', size=11)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== TAB 3: TOP 3 ==========
    with tab3:
        st.markdown("### 📊 COMPARACIÓN TOP 3")
        
        top3 = resultados.head(3)['PILOTO'].tolist()
        
        fig = go.Figure()
        colores_top = ['#FFD700', '#C0C0C0', '#CD7F32']
        
        for driver, color in zip(top3, colores_top):
            driver_laps = session.laps.pick_driver(driver)
            driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
            
            fig.add_trace(go.Scatter(
                x=driver_laps['LapNumber'],
                y=driver_laps['LapTimeSeconds'],
                mode='lines+markers',
                name=driver,
                line=dict(color=color, width=3),
                marker=dict(size=5)
            ))
        
        fig.update_layout(
            template='plotly_dark',
            height=600,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#000000',
            font=dict(color='white', size=11),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== TAB 4: ESTADÍSTICAS ==========
    with tab4:
        st.markdown("### 📈 ESTADÍSTICAS GENERALES")
        
        all_laps = session.laps
        all_laps['LapTimeSeconds'] = all_laps['LapTime'].dt.total_seconds()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏁 TOTAL VUELTAS", len(all_laps))
        with col2:
            st.metric("⚡ VUELTA RÁPIDA", f"{all_laps['LapTimeSeconds'].min():.2f}s")
        with col3:
            st.metric("📊 PROMEDIO", f"{all_laps['LapTimeSeconds'].mean():.2f}s")
        
        st.markdown("---")
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=all_laps['LapTimeSeconds'].dropna(),
            nbinsx=50,
            marker=dict(color=F1_RED, line=dict(color='white', width=1))
        ))
        
        fig.update_layout(
            title='Distribución de Tiempos',
            template='plotly_dark',
            height=500,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#000000',
            font=dict(color='white', size=11),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== TAB 5: ANÁLISIS ==========
    with tab5:
        st.markdown("### 🔍 ANÁLISIS AVANZADO")
        
        pilotos_compare = st.multiselect(
            "Selecciona pilotos para comparar:",
            resultados['PILOTO'].tolist(),
            default=resultados['PILOTO'].tolist()[:3],
            max_selections=6
        )
        
        if pilotos_compare:
            fig = go.Figure()
            
            for pilot in pilotos_compare:
                pilot_laps = session.laps.pick_driver(pilot)
                pilot_laps['LapTimeSeconds'] = pilot_laps['LapTime'].dt.total_seconds()
                
                fig.add_trace(go.Scatter(
                    x=pilot_laps['LapNumber'],
                    y=pilot_laps['LapTimeSeconds'],
                    mode='lines+markers',
                    name=pilot,
                    line=dict(width=2.5),
                    marker=dict(size=5)
                ))
            
            fig.update_layout(
                template='plotly_dark',
                height=600,
                plot_bgcolor='#1a1a1a',
                paper_bgcolor='#000000',
                font=dict(color='white', size=11),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)

else:
    st.markdown(f"""
    <div style='text-align: center; padding: 50px; background: {F1_GRAY}; border-radius: 10px; margin: 20px 0;'>
        <div style='font-size: 3em; margin: 20px 0;'>🏎️</div>
        <h2 style='color: {F1_RED};'>SELECCIONA UNA CARRERA</h2>
        <p style='color: #999; font-size: 1.1em;'>Usa el menú de la izquierda para elegir año y Gran Premio</p>
    </div>
    """, unsafe_allow_html=True)

# FOOTER
st.markdown("---")
st.markdown(f"""
    <div style='text-align: center; padding: 20px; color: #666; font-size: 0.9em;'>
        <p><strong>Formula 1 Analytics Pro</strong></p>
        <p>Proyecto: From the Track to the Code</p>
        <p>Programación y Ciencia Computacional 2025-2</p>
        <p>Universidad de Antioquia - Ingeniería Aeroespacial</p>
        <p style='margin-top: 10px; font-size: 0.85em;'>Jeronimo Casallas | Karol Escobar | Sharon Ramírez</p>
    </div>
""", unsafe_allow_html=True)