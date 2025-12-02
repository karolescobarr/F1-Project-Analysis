import streamlit as st
import os

# ==============================
# CONFIGURACIÓN DE PÁGINA
# ==============================
st.set_page_config(
    page_title="F1 Simulator - Proyecto Final",
    page_icon="🏎️",
    layout="centered"
)

# ==============================
# ESTILO GLOBAL (AZUL-GRIS)
# ==============================
st.markdown("""
    <style>
        body {
            background-color: #0f172a;
            color: #e2e8f0;
        }
        .title {
            text-align: center;
            font-size: 40px;
            font-weight: bold;
            color: #3b82f6;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 18px;
            color: #94a3b8;
            margin-bottom: 30px;
        }
        .stButton>button {
            width: 100%;
            background-color: #1e3a8a;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-size: 18px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #3b82f6;
            color: white;
        }
        .userbox {
            background-color: #1e293b;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 15px;
            color: #93c5fd;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================
# LOGIN SIMULADO
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Mostrar logo de F1 centrado
    st.image("assets/logo_f1.png", width=200)
    st.markdown("<div class='title'>Simulador de Estrategias en Fórmula 1</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Inicio de sesión</div>", unsafe_allow_html=True)


    with st.form("login_form"):
        nombre = st.text_input("👤 Nombre del usuario:")
        rol = st.selectbox("🎯 Rol en el simulador:", ["Piloto", "Ingeniero de pista"])
        entrar = st.form_submit_button("Entrar al sistema")

        if entrar:
            if nombre.strip() == "":
                st.warning("Por favor ingresa tu nombre antes de continuar.")
            else:
                st.session_state.nombre = nombre
                st.session_state.rol = rol
                st.session_state.logged_in = True
                st.success(f"¡Bienvenido {nombre}! 🚀")
                st.rerun()
else:
    # ==============================
    # MENÚ PRINCIPAL
    # ==============================
    st.markdown(f"<div class='userbox'>Usuario: <b>{st.session_state.nombre}</b> | Rol: {st.session_state.rol}</div>", unsafe_allow_html=True)
    st.markdown("<div class='title'>Panel Principal</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Proyecto Final - Ingeniería Aereoespacial (UDEA)</div>", unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏁 Simulador de Carrera"):
            os.system("py -m streamlit run simulador.py")

    with col2:
        if st.button("📊 Análisis Real F1"):
            os.system("py -m streamlit run analisis_real.py")

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        if st.button("🔄 Cerrar sesión"):
            st.session_state.logged_in = False
            st.rerun()

    with col4:
        st.markdown("<center><small style='color:#94a3b8;'>Versión 2.0 - 2025</small></center>", unsafe_allow_html=True)
