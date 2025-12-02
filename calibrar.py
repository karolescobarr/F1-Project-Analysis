# calibrar.py
# -------------------------
# IMPORTANTE: adapta rutas si es necesario y asegúrate de tener fastf1 instalado.
# Ejecuta: py -m python calibrar.py
# -------------------------

import fastf1
import fastf1.core
import numpy as np
import pandas as pd
import json
import os
from math import sqrt
import random
import time

# -------- CONFIG ----------
fastf1.Cache.enable_cache("fastf1_cache")  # ya la creaste
YEAR = 2024
GP = "Monza"           # cambia según lo que quieras calibrar
DRIVER = None          # si None tomará el primer piloto de la carrera
N_SIM_PER_CONFIG = 4   # repeticiones por configuración
SIMULATOR_MODULE = "simulador"  # nombre del módulo/archivo si invocas función; en este script usaremos otra estrategia (ver abajo)
# --------------------------

# Carga datos reales con FastF1
print("Cargando datos reales (FastF1)... esto puede tardar...")
session = fastf1.get_session(YEAR, GP, 'R')
session.load()

laps = session.laps
# si DRIVER none, tomamos el primer driver de la lista
drivers = list(session.drivers)
if DRIVER is None:
    driver = drivers[0]
else:
    driver = DRIVER

laps_driver = session.laps.pick_driver(driver)
# eliminar vueltas sin tiempo válido
laps_driver = laps_driver[laps_driver['LapTime'].notnull()]

mean_real = laps_driver['LapTime'].dt.total_seconds().mean()
fastest_real = laps_driver['LapTime'].dt.total_seconds().min()
print(f"Referencia real ({GP} {YEAR}, piloto {driver}): mean={mean_real:.3f}s, fastest={fastest_real:.3f}s, laps={len(laps_driver)}")

# ------------------------------------------------------------
# Función "wrapper" para simular: aquí simplificamos llamando
# al simulador como un subprocess sería posible, pero lo más
# sencillo para evitar integraciones complejas es importar la
# función de simulación si la hiciste modular. Si no, puedes
# adaptar la parte de simulación de tu simulador.py en una
# función reutilizable y luego importarla aquí.
# ------------------------------------------------------------

# Para este ejemplo asumimos que en simulador.py definiste una función:
# simulate_once(track_dict, motor_choice, aero_choice, tyre_seq, pitlane_time, clima_key)
# que devuelve dict con 'lap_times' y 'total_time_s'.
# Si no la tienes así, copia la lógica mínima de simulate_strategy_advanced
# en una función aquí o adapta el script.

# >>> ADAPTA LA SIGUIENTE FUNCION A TU IMPLEMENTACION LOCAL:
def simulate_wrapper(track, motor_choice, aero_choice, tyre_seq, pitlane_time, clima_key, seed=None):
    """
    Debes adaptar esta función: puede importar tu simulador.py si defines
    simulate_strategy_advanced como función allí. Aquí mostramos una
    versión de ejemplo que simplemente llama a simulador.simulate_strategy_advanced.
    """
    import simulador as simmod  # tu archivo simulador.py debe estar en mismo folder
    # fija semilla para reproducibilidad ligera
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    result = simmod.simulate_strategy_advanced(track, {"motor": simmod.MOTOR_OPTIONS[motor_choice], "aero": simmod.AERO_OPTIONS[aero_choice]}, tyre_seq, pitlane_time, clima_key, weather_dynamic=False, show_progress=False)
    return result

# ------------------------------------------------------------
# Preparar el objeto 'track' a usar (leer data/circuitos.json)
# ------------------------------------------------------------
with open("data/circuitos.json", "r", encoding="utf-8") as f:
    circuits = json.load(f)

# toma la referencia del circuito
if GP not in circuits:
    print("GP no encontrado en data/circuitos.json. Edita y añade la pista o cambia GP.")
    raise SystemExit

track_ref = circuits[GP]

# Valores base actuales
current_base = track_ref["tiempo_base_s"]
print(f"Tiempo base actual en JSON: {current_base}s")

# Rango para buscar (ejemplo)
base_candidates = np.arange(current_base * 0.95, current_base * 1.05 + 0.01, 0.5)  # pasos de 0.5s
degr_candidates = np.arange(0.006, 0.018, 0.001)  # ejemplo para C3 - ajusta según neumático objetivo

# elige un neumático objetivo para calibrar degradación (ej. C3 o C2)
tyre_to_calibrate = "C3"

best = None
best_config = None
evals = 0
start_time = time.time()

for base_c in base_candidates:
    # parche: actualizar temporalmente el campo en track_ref para la simulación
    track_tmp = dict(track_ref)
    track_tmp["tiempo_base_s"] = float(base_c)

    for degr_c in degr_candidates:
        # modificar temporalmente en el objeto global de neumáticos:
        # aqui actualizamos el archivo neumaticos.json en memoria y luego lo restablecemos
        with open("data/neumaticos.json", "r", encoding="utf-8") as f:
            tyres_all = json.load(f)
        tyres_all[tyre_to_calibrate]["degradation_per_lap"] = float(degr_c)
        # Guardamos temporalmente en disco (opcional) o inyectamos en memoria
        with open("data/neumaticos.json", "w", encoding="utf-8") as f:
            json.dump(tyres_all, f, indent=2)

        # Ejecutar N_SIM_PER_CONFIG simulaciones y promediar
        means = []
        fastest = []
        for i in range(N_SIM_PER_CONFIG):
            seed = i * 12345 + int(base_c*10) + int(degr_c*1000)
            # ejemplo de llamada: motor Equilibrado, aero Medio, tyre_seq = ['C3']*(laps/n_stints)
            motor_choice = "Equilibrado"
            aero_choice = "Medio"
            # construir tyre_seq simple: repartir las vueltas en 1 stint (o pitstops según quieres medir)
            tyre_seq = ["C3"]  # para medir efecto, usa 1 stint para simplificar
            res = simulate_wrapper(track_tmp, motor_choice, aero_choice, tyre_seq, track_tmp.get("pitlane_time_s",22.0), "Seco", seed=seed)
            lap_times_only = [x for x in res["lap_times"] if isinstance(x, (int, float))]
            means.append(np.mean(lap_times_only))
            fastest.append(np.min(lap_times_only))
        mean_sim = float(np.mean(means))
        fastest_sim = float(np.mean(fastest))
        loss = sqrt((mean_real - mean_sim)**2 + (fastest_real - fastest_sim)**2)

        evals += 1
        if best is None or loss < best:
            best = loss
            best_config = {"base": base_c, "degradation": degr_c, "mean_sim": mean_sim, "fastest_sim": fastest_sim, "loss": loss}
        # opcional: print cada X evaluaciones
        if evals % 20 == 0:
            print(f"Ite {evals}: base={base_c}, degr={degr_c}, mean_sim={mean_sim:.3f}, loss={loss:.3f}")

# restaurar neumaticos.json a la versión original si quieres (mejor tener respaldo)
# (asumimos que tienes backup o control de versiones)

elapsed = time.time() - start_time
print("----- FIN GRID SEARCH -----")
print(f"Evaluaciones: {evals}, tiempo: {elapsed:.1f}s")
print("Mejor configuración encontrada:")
print(best_config)

# sugerencia: escribir los valores finales en data/circuitos.json y data/neumaticos.json
apply_change = input("Deseas aplicar estos valores al archivo JSON? (s/n): ").strip().lower()
if apply_change == "s":
    # actualizar circuito
    with open("data/circuitos.json", "r", encoding="utf-8") as f:
        circuits_all = json.load(f)
    circuits_all[GP]["tiempo_base_s"] = float(best_config["base"])
    with open("data/circuitos.json", "w", encoding="utf-8") as f:
        json.dump(circuits_all, f, indent=2)

    # actualizar neumático calibrado
    with open("data/neumaticos.json", "r", encoding="utf-8") as f:
        tyres_all = json.load(f)
    tyres_all[tyre_to_calibrate]["degradation_per_lap"] = float(best_config["degradation"])
    with open("data/neumaticos.json", "w", encoding="utf-8") as f:
        json.dump(tyres_all, f, indent=2)

    print("Archivos actualizados. Recomendado: probar con otra carrera para validação.")
else:
    print("No se aplicaron cambios.")
