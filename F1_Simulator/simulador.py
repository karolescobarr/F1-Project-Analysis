"""
Simulador Nivel 2 - versión avanzada (clima dinámico, temperatura/desgaste, penalizaciones, podio)
- Interfaz Streamlit
- Permite comparar 1 o 2 estrategias y ver un ranking final
- Guarda CSV si lo deseas
"""

import streamlit as st
import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random

# -----------------------------
# CONFIG Y CARGA DE DATOS
# -----------------------------
DATA_DIR = "data"
RESULTS_DIR = "resultados"
os.makedirs(RESULTS_DIR, exist_ok=True)

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

circuitos = load_json("circuitos.json")
neumaticos = load_json("neumaticos.json")

# -----------------------------
# Parámetros y opciones
# -----------------------------
MOTOR_OPTIONS = {
    "Equilibrado": {"potencia": 1.00, "tyre_wear_factor": 1.00},
    "Potente": {"potencia": 1.05, "tyre_wear_factor": 1.10},
    "Eficiente": {"potencia": 0.97, "tyre_wear_factor": 0.90}
}

AERO_OPTIONS = {
    "Bajo": {"aero": 0.95},
    "Medio": {"aero": 1.00},
    "Alto": {"aero": 1.05}
}

CLIMA_OPTIONS = {
    "Seco": {"grip_weather": 1.00, "rain": False},
    "Nublado": {"grip_weather": 0.97, "rain": False},
    "Lluvia ligera": {"grip_weather": 0.88, "rain": True},
    "Lluvia intensa": {"grip_weather": 0.75, "rain": True}
}

# Model params (ajustables)
K_GRIP = 0.08
K_WEAR = 1.6
RANDOM_NOISE_STD = 0.12  # variabilidad por vuelta (s)
PIT_ERROR_CHANCE = 0.02  # probabilidad de error en un pit (por pitstop)
SPIN_CHANCE_BASE = 0.01   # probabilidad base de salida en lluvia por vuelta (aumenta si slicks)

# -----------------------------
# FUNCIONES AUXILIARES
# -----------------------------
def base_lap_time(track, motor_coef, aero_coef):
    return track["tiempo_base_s"] / (motor_coef * aero_coef)

def tyre_suitability_penalty(tyre_key, is_raining):
    """Devuelve multiplicador y riesgo extra si neumático es inadecuado para la lluvia"""
    if is_raining:
        if tyre_key in ["Intermedio", "Lluvia"]:
            return 1.0, 0.0  # adecuado
        else:
            # Slicks en lluvia -> penalidad y riesgo de salida
            return 1.15, 0.02  # +15% tiempo por vuelta y +2% de spin chance
    else:
        # Si usas rain tyres en seco penaliza un poco (menos temperatura ideal)
        if tyre_key == "Lluvia":
            return 1.08, 0.0
        return 1.0, 0.0

def simulate_strategy_advanced(track, car_setup, tyre_sequence, pitlane_time, initial_clima_key,
                               weather_dynamic=True, show_progress=False):
    """
    Simulación avanzada:
    - Puede cambiar el clima (weather_dynamic=True)
    - Modela temperatura de neumático y penalizaciones
    - Retorna dict con lap_times, details, total_time, events, final_clima
    """
    laps_total = track["vueltas"]
    n_stints = len(tyre_sequence)
    base = laps_total // n_stints
    remainder = laps_total % n_stints
    stints_laps = [base + (1 if i < remainder else 0) for i in range(n_stints)]

    motor_coef = car_setup["motor"]["potencia"]
    aero_coef = car_setup["aero"]["aero"]
    tyre_wear_factor = car_setup["motor"]["tyre_wear_factor"]

    lap_times = []
    details = []
    lap_number = 1
    base_time = base_lap_time(track, motor_coef, aero_coef)

    # clima inicial
    clima_key = initial_clima_key
    clima = CLIMA_OPTIONS[clima_key]

    # progress UI
    if show_progress:
        progress_bar = st.progress(0)
        progress_text = st.empty()

    # estado de neumático: temperatura (°C) y grip aproximado
    # asumimos temp óptima 85°C; temperatura sube si llegas a usar duro con altas cargas etc.
    # Simplificamos: temp starts at 70
    tyre_temp = 70.0

    # evento log (p. ej. cambios de clima, spins, pit errors)
    events = []

    for stint_idx, tyre_key in enumerate(tyre_sequence):
        tyre = neumaticos[tyre_key]
        # grip inicial modulada por clima
        grip_initial = tyre["grip_initial"] * clima["grip_weather"]
        degr_base = tyre["degradation_per_lap"] * tyre_wear_factor * track["abrasion"]
        speed_factor = tyre.get("speed_factor", 1.0)
        laps_in_stint = stints_laps[stint_idx]

        for v in range(1, laps_in_stint + 1):
            # posible cambio climático (si está activado)
            if weather_dynamic and random.random() < 0.03:  # 3% chance per lap to change weather
                # simple transition: if not raining -> 30% chance start rain; if raining -> 50% chance stop
                if clima["rain"]:
                    # stop rain
                    if random.random() < 0.5:
                        clima_key = "Seco"
                        clima = CLIMA_OPTIONS[clima_key]
                        events.append({"lap": lap_number, "event": "Rain stopped -> Seco"})
                else:
                    if random.random() < 0.3:
                        clima_key = random.choice(["Lluvia ligera", "Lluvia intensa"])
                        clima = CLIMA_OPTIONS[clima_key]
                        events.append({"lap": lap_number, "event": f"Started {clima_key}"})

            # actualizar tyre_temp de forma simplificada
            # temp aumenta con cada vuelta y con mayor aero/power; baja si lluvia
            tyre_temp += 0.8 * motor_coef * aero_coef  # sube por uso
            if clima["rain"]:
                tyre_temp -= 2.5  # lluvia enfría algo
            # acercar a un mínimo máximo
            tyre_temp = max(40.0, min(120.0, tyre_temp))

            # grip se ve afectado por tyre_temp (óptimo ~85)
            temp_penalty = max(0.0, abs(tyre_temp - 85.0) / 150.0)  # penaliza desviaciones
            # grip en esta vuelta (no menor que 0.25)
            grip = max(0.25, grip_initial - degr_base * (v - 1) - temp_penalty)

            # aplicamos la penalidad por uso de neumático inadecuado y riesgo de spin
            pen_mult, extra_spin_risk = tyre_suitability_penalty(tyre_key, clima["rain"])
            # spin chance base aumentada si grip muy bajo
            spin_chance = SPIN_CHANCE_BASE + extra_spin_risk + max(0.0, (0.5 - grip)) * 0.05

            # compute lap time
            lap_time = base_time * (1 / speed_factor) * (1 - K_GRIP * grip) + K_WEAR * (1 - grip)
            lap_time *= pen_mult
            lap_time += float(np.random.normal(0, RANDOM_NOISE_STD))
            lap_time = max(0.1, lap_time)

            # check spin event (only in rain or very low grip)
            spin = False
            if random.random() < spin_chance:
                spin = True
                spin_delay = random.uniform(15.0, 60.0)  # seconds lost in spin/recovery
                lap_time += spin_delay
                events.append({"lap": lap_number, "event": f"Spin! +{spin_delay:.1f}s", "tyre": tyre_key})

            lap_times.append(lap_time)
            details.append({
                "lap": lap_number,
                "stint": stint_idx + 1,
                "tyre": tyre_key,
                "grip": round(grip, 4),
                "temp": round(tyre_temp, 1),
                "lap_time_s": round(lap_time, 3),
                "clima": clima_key
            })
            lap_number += 1

            # update UI progress
            if show_progress:
                percent = int(100 * ((lap_number - 1) / (laps_total + (n_stints - 1))))  # include pits approximate
                progress_bar.progress(percent)
                progress_text.markdown(f"🏎️ Stint {stint_idx+1}/{n_stints} — Vuelta {v}/{laps_in_stint} — Clima: **{clima_key}**")

        # pitstop (if not last stint)
        if stint_idx < n_stints - 1:
            # chance of pit error
            pit_time = pitlane_time
            if random.random() < PIT_ERROR_CHANCE:
                extra = random.uniform(5.0, 12.0)
                pit_time += extra
                events.append({"lap": lap_number, "event": f"Pit error +{extra:.1f}s"})
            # pit as an event (we store as a lap entry)
            lap_times.append(pit_time)
            details.append({
                "lap": lap_number,
                "stint": "PIT",
                "tyre": "Cambio",
                "grip": None,
                "temp": None,
                "lap_time_s": round(pit_time, 3),
                "clima": clima_key
            })
            lap_number += 1
            # pit causes tyre temp reset (fresh tyres)
            tyre_temp = 70.0

    total_time = sum(lap_times)
    if show_progress:
        progress_bar.empty()
        progress_text.empty()
    return {
        "lap_times": lap_times,
        "total_time_s": total_time,
        "details": details,
        "stints_laps": stints_laps,
        "events": events,
        "final_clima": clima_key
    }

# -----------------------------
# INTERFAZ STREAMLIT
# -----------------------------
st.set_page_config(page_title="Simulador F1 - Avanzado", page_icon="🏁", layout="centered")
st.markdown("<h1 style='color:#3b82f6;text-align:center;'>Simulador Avanzado - F1</h1>", unsafe_allow_html=True)
st.divider()

# Selección base (misma para principal y comparador)
colA, colB = st.columns([2, 1])
with colA:
    circuito_name = st.selectbox("Selecciona circuito", list(circuitos.keys()))
    track = circuitos[circuito_name]
    st.write(f"Vueltas: **{track['vueltas']}** — Longitud: {track['longitud_km']} km")
with colB:
    motor_choice = st.selectbox("Tipo de motor", list(MOTOR_OPTIONS.keys()))
    aero_choice = st.selectbox("Nivel de alerones", list(AERO_OPTIONS.keys()))
    clima_choice = st.selectbox("Clima inicial", list(CLIMA_OPTIONS.keys()))

pitstops = st.slider("Número de pitstops", min_value=0, max_value=3, value=1)
n_stints = pitstops + 1

st.markdown(f"### Selección de neumáticos (Estr. principal) — {n_stints} stints")
cols = st.columns(n_stints)
tyre_sequence = []
tyre_keys = list(neumaticos.keys())
for i in range(n_stints):
    with cols[i]:
        tyre_sequence.append(st.selectbox(f"Stint {i+1}", tyre_keys, key=f"main_tyre_{i}"))

# Comparar con estrategia alternativa?
compare = st.checkbox("Comparar con una estrategia alternativa (ejecuta 2 simulaciones)")

alt_tyres = []
if compare:
    st.markdown(f"### Estrategia alternativa — {n_stints} stints")
    cols2 = st.columns(n_stints)
    for i in range(n_stints):
        with cols2[i]:
            alt_tyres.append(st.selectbox(f"Alt Stint {i+1}", tyre_keys, key=f"alt_tyre_{i}"))
else:
    alt_tyres = None

st.divider()
col_run, col_save = st.columns([2,1])
with col_run:
    run_sim = st.button("🏁 Ejecutar simulación avanzada")
with col_save:
    save_csv = st.button("💾 Guardar última(s) simulación(es)")

# mostrar resumen config
st.markdown("#### Configuración seleccionada:")
st.json({
    "Circuito": circuito_name,
    "Motor": motor_choice,
    "Alerones": aero_choice,
    "Clima inicio": clima_choice,
    "Pitstops": pitstops,
    "Neumáticos principal": tyre_sequence,
    "Comparar": compare,
    "Neumáticos alterna": alt_tyres if compare else "N/A"
})

# Ejecutar
if run_sim:
    st.info("Ejecutando simulaciones... espera unos segundos.")
    car_setup = {"motor": MOTOR_OPTIONS[motor_choice], "aero": AERO_OPTIONS[aero_choice]}

    # Ejecutar principal
    result_main = simulate_strategy_advanced(track, car_setup, tyre_sequence, track.get("pitlane_time_s",22.0), clima_choice, weather_dynamic=True, show_progress=True)

    # Ejecutar alternativa si aplica
    result_alt = None
    if compare and alt_tyres:
        # pequeña pausa para que no interfieran random seeds demasiado parecidos
        result_alt = simulate_strategy_advanced(track, car_setup, alt_tyres, track.get("pitlane_time_s",22.0), clima_choice, weather_dynamic=True, show_progress=True)

    # Mostrar resultados individuales
    def show_result_block(name, result):
        total_min = result["total_time_s"] / 60.0
        st.success(f"Resultado — {name}: **{total_min:.2f} minutos** ({result['total_time_s']:.1f} s)")
        # gráfico ritmo
        fig, ax = plt.subplots(figsize=(10,3))
        ax.plot(result["lap_times"], marker='o', linewidth=1)
        ax.set_title(f"Ritmo por vuelta - {name}")
        ax.set_xlabel("Evento (vuelta/pit)")
        ax.set_ylabel("Tiempo (s)")
        ax.grid(True)
        st.pyplot(fig)
        # events
        if result["events"]:
            st.markdown("**Eventos relevantes:**")
            for e in result["events"]:
                st.markdown(f"- Vuelta {e['lap']}: {e['event']}")
        else:
            st.markdown("**Eventos relevantes:** Ninguno")
        # tabla detalle top
        df = pd.DataFrame(result["details"])
        st.markdown("Detalle (primeras 20 filas):")
        st.dataframe(df.head(20))
        # metrics
        lap_times_only = [x for x in result["lap_times"] if isinstance(x, (int, float))]
        mean = np.mean(lap_times_only)
        fastest = np.min(lap_times_only)
        consistency = np.std(lap_times_only)
        st.markdown(f"- Tiempo promedio por vuelta: **{mean:.2f} s**")
        st.markdown(f"- Vuelta más rápida (evento): **{fastest:.2f} s**")
        st.markdown(f"- Consistencia (desviación estándar): **{consistency:.2f} s**")

    show_result_block("Estrategia Principal", result_main)
    if result_alt:
        show_result_block("Estrategia Alternativa", result_alt)

    # Podio / ranking entre estrategias
    ranking = []
    ranking.append(("Principal", result_main["total_time_s"], tyre_sequence))
    if result_alt:
        ranking.append(("Alternativa", result_alt["total_time_s"], alt_tyres))
    ranking_sorted = sorted(ranking, key=lambda x: x[1])
    st.divider()
    st.markdown("## 🏁 Ranking final (mejor a peor)")
    for i, r in enumerate(ranking_sorted, start=1):
        minutes = r[1] / 60.0
        st.markdown(f"**{i}. {r[0]}** — {minutes:.2f} min — Neumáticos: {r[2]}")

    # Guardar resultados en session_state para descarga
    st.session_state["last_sim_main"] = {"config": {"circuito": circuito_name, "motor": motor_choice, "alerones": aero_choice, "clima": clima_choice, "pitstops": pitstops, "tyre_sequence": tyre_sequence}, "result": result_main}
    if result_alt:
        st.session_state["last_sim_alt"] = {"config": {"circuito": circuito_name, "motor": motor_choice, "alerones": aero_choice, "clima": clima_choice, "pitstops": pitstops, "tyre_sequence": alt_tyres}, "result": result_alt}

# Guardar CSV
if save_csv:
    saved = []
    if "last_sim_main" in st.session_state:
        d = st.session_state["last_sim_main"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"sim_{d['config']['circuito']}_main_{timestamp}.csv"
        pd.DataFrame(d["result"]["details"]).to_csv(os.path.join(RESULTS_DIR, fname), index=False)
        saved.append(fname)
    if "last_sim_alt" in st.session_state:
        d = st.session_state["last_sim_alt"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"sim_{d['config']['circuito']}_alt_{timestamp}.csv"
        pd.DataFrame(d["result"]["details"]).to_csv(os.path.join(RESULTS_DIR, fname), index=False)
        saved.append(fname)
    if saved:
        st.success(f"Guardado(s): {', '.join(saved)}")
    else:
        st.warning("No hay simulaciones en memoria para guardar. Ejecuta una simulación primero.")

st.divider()
st.markdown("<small style='color:#94a3b8;'>Nivel 2: clima dinámico, temperatura de neumáticos y podio - Proyecto F1</small>", unsafe_allow_html=True)
