===========================================
        F1 SIMULATOR – INSTRUCCIONES
===========================================

Este proyecto es un simulador avanzado de estrategias
de Fórmula 1 desarrollado en Python y Streamlit.
Permite probar neumáticos, clima, setups y variables
de carrera para generar recomendaciones basadas en
simulaciones dinámicas.

Este archivo explica cómo ejecutar el proyecto desde
cualquier computador con Python instalado.

-------------------------------------------
1. REQUISITOS NECESARIOS
-------------------------------------------

✔ Python 3.11 o superior (compatible con 3.13.5)
✔ Pip (gestor de paquetes de Python)
✔ Conexión a internet (FastF1 descarga datos reales)
✔ Las dependencias del archivo requirements.txt

-------------------------------------------
2. INSTALACIÓN DE DEPENDENCIAS
-------------------------------------------

1. Abrir una terminal en la carpeta del proyecto:

   F1_SIMULATOR/

2. Ejecutar el siguiente comando:

   pip install -r requirements.txt

Esto instalará automáticamente:

- streamlit
- fastf1
- pandas
- numpy
- matplotlib
- requests
- plotly

Si usas Windows y Python 3.13, usa:

   python -m pip install -r requirements.txt

-------------------------------------------
3. EJECUTAR EL SIMULADOR
-------------------------------------------

Una vez instaladas las dependencias:

1. Ubicarse en la carpeta del proyecto
2. Ejecutar:

   streamlit run main.py

Esto abrirá la aplicación en el navegador en la dirección:

   http://localhost:8501

-------------------------------------------
4. ESTRUCTURA DEL PROYECTO
-------------------------------------------

F1_SIMULATOR/
│
├── main.py               → Interfaz principal Streamlit
├── simulador.py          → Lógica de simulación de carreras
├── analisis_real.py      → Módulo para cargar datos reales con FastF1
│
├── assets/
│   └── logo_f1.png       → Imagen del logo para la interfaz
│
├── data/
│   ├── circuitos.json    → Información de circuitos
│   └── neumaticos.json   → Datos de neumáticos
│
├── fastf1_cache/         → Caché obligatorio de FastF1
│
└── resultados/           → Guardado de simulaciones en CSV

-------------------------------------------
5. NOTAS IMPORTANTES
-------------------------------------------

✔ La carpeta fastf1_cache NO se debe borrar.
  FastF1 requiere esa carpeta para funcionar.

✔ Si aparece un error de caché:
  Crear manualmente la carpeta "fastf1_cache"
  en la raíz del proyecto.

✔ Para detener el simulador:
  Presionar CTRL + C en la terminal.

-------------------------------------------
6. SOPORTE / ERRORES COMUNES
-------------------------------------------

• "Streamlit no se reconoce como comando":
  → Instala streamlit manualmente:
      pip install streamlit

• Error de FastF1 sobre la caché:
  → Asegúrate de que existe:
      F1_SIMULATOR/fastf1_cache/

• Si la app no abre automáticamente:
  → Abre manualmente el link:
      http://localhost:8501

-------------------------------------------
7. CRÉDITOS
-------------------------------------------

Proyecto universitario desarrollado para simular
estrategias de carrera en Fórmula 1 con:
- Streamlit
- FastF1
- Python 3.13

===========================================
 FIN DEL README
===========================================
