"""
================================================================================
AWQPE PROTOCOL DASHBOARD v2.0
Adaptive Windowed Quantum Phase Estimation & T-QNN Integration
================================================================================
"""

import os
import time
import sys
import numpy as np

# Intento de importar módulos para ejecución en vivo
try:
    from t_qnn import TopologicalQNN_AWQPE
    from confinamiento import QuantumConfinementModel
except ImportError:
    # Fallback si no están en el path
    pass

# ============================================================================
# CONTENIDO TEÓRICO (PRE-CARGADO)
# ============================================================================

THEORY_SECTIONS = {
    "1": {
        "title": "Introducción Teórica",
        "content": """
MARCO TEÓRICO:
==============
El Protocolo AWQPE (Adaptive Windowed Quantum Phase Estimation) mejora
el algoritmo QPEA estándar mediante:

1. VENTANAS ADAPTATIVAS:
   - Divide la precisión total en bloques pequeños.
   - Reduce requisitos de coherencia (Coherence Margin).

2. ESTIMACIÓN CON CORRECCIÓN DE ERRORES:
   - Detecta ambigüedades mediante ratio de probabilidades.
   - Aplica correcciones LSB-to-MSB dinámicas.

3. VALIDACIÓN FÍSICA:
   - Verifica límites de hardware en tiempo real.
   - Métricas de confianza Bayesiana integradas.
"""
    },
    "2": {
        "title": "Arquitectura del Protocolo",
        "content": """
ESTRUCTURA EN FASES:

I.  PREPARACIÓN (SETUP): Definición de U|u⟩ y estrategia de ventanas.
II. EJECUCIÓN: Phase Kickback + IQFT por bloque.
III.RESOLUCIÓN DE AMBIGÜEDAD: Lógica Bayesiana + Mahalanobis.
IV. RECONSTRUCCIÓN: Concatenación de bits y validación física.
"""
    },
    "3": {
        "title": "Metodología Avanzada (Nueva)",
        "content": """
MEJORAS DE ÚLTIMA GENERACIÓN:

1. DISTANCIA DE MAHALANOBIS:
   - Utiliza la matriz de covarianza del histograma para evaluar candidatos.
   - Ignora ruido no correlacionado.

2. LOGICA BAYESIANA:
   - Prior basado en la matriz de transición de momentos.
   - Posterior modulado por la verosimilitud (Likelihood) física.

3. COSENOS DIRECTORES:
   - Proyección del estado en una base 3D (Entropía, Coherencia, Estabilidad).
   - Estabilización mediante Operador Áureo (Golden Ratio).
"""
    }
}

# ============================================================================
# LÓGICA DE LA INTERFAZ (DASHBOARD)
# ============================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("\033[1;34m" + "=" * 80 + "\033[0m")
    print("\033[1;36m      AWQPE PROTOCOL DASHBOARD v2.0 - PROFESSIONAL SYSTEM\033[0m")
    print("\033[1;34m" + "=" * 80 + "\033[0m")
    print(f"      Status: ONLINE | Precision: ADAPTIVE | Methodology: BAYES-MAHALANOBIS")
    print("\033[1;34m" + "=" * 80 + "\033[0m\n")

def main_menu():
    clear_screen()
    print_header()
    print(" SELECCIONE UNA OPCIÓN:\n")
    print(" [1] Leer Introducción Teórica")
    print(" [2] Arquitectura del Protocolo")
    print(" [3] Metodología Avanzada (Bayes/Mahalanobis)")
    print(" [4] EJECUTAR: Simulación T-QNN + AWQPE (Live)")
    print(" [5] EJECUTAR: Modelo de Confinamiento Cuántico")
    print(" [6] Ver Referencias y Lectura Adicional")
    print(" [0] Salir del Sistema")
    print("\n" + "=" * 80)
    return input("\n > Opción: ")

def show_theory(section_id):
    section = THEORY_SECTIONS.get(section_id)
    if not section: return
    
    clear_screen()
    print_header()
    print(f" --- {section['title'].upper()} ---\n")
    print(section['content'])
    print("\n" + "=" * 80)
    input("\nPresione ENTER para volver al menú...")

def run_t_qnn_sim():
    clear_screen()
    print_header()
    print(" --- EJECUTANDO SIMULACIÓN T-QNN + AWQPE INTEGRADA ---\n")
    print("[*] Inicializando Registros Cuánticos...")
    time.sleep(0.5)
    print("[*] Configurando Resolver Bayesiano con Distancia de Mahalanobis...")
    time.sleep(0.5)
    
    try:
        qnn = TopologicalQNN_AWQPE()
        # Caso de prueba: Momento 1
        features = np.array([1.5, 1.3, 1.2])
        print(f"[*] Procesando Features: {features}")
        result = qnn.measure_moment(features, shots=1024)
        print(qnn.generate_report(result))
    except NameError:
        print("\033[1;31mError: El módulo t_qnn no pudo ser cargado.\033[0m")
    
    print("\n" + "=" * 80)
    input("\nPresione ENTER para volver al menú...")

def run_confinement_model():
    clear_screen()
    print_header()
    print(" --- EJECUTANDO MODELO DE CONFINAMIENTO CUÁNTICO (confinamiento.py) ---\n")
    
    try:
        model = QuantumConfinementModel(verbose=True)
        counts = model.run_simulation(shots=1024)
        model.analyze_results(counts)
    except NameError:
        print("\033[1;31mError: El módulo confinamiento no pudo ser cargado.\033[0m")
    except Exception as e:
        print(f"\033[1;31mError en la simulación: {e}\033[0m")
        print("Asegúrese de tener Qiskit instalado.")
    
    print("\n" + "=" * 80)
    input("\nPresione ENTER para volver al menú...")

def show_references():
    clear_screen()
    print_header()
    print(" --- REFERENCIAS Y LECTURA ADICIONAL ---\n")
    print("[1] Kitaev, A. Y. (1995) - Abelian Stabilizer Problem")
    print("[2] Berry, M. V. (1984) - Quantal phase factors")
    print("[3] QuoreMind v1.0.0 - Metriplectic Quantum-Bayesian Structure")
    print("\nRepositorio: https://github.com/quantum-research/awqpe")
    print("\n" + "=" * 80)
    input("\nPresione ENTER para volver al menú...")

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def start_dashboard():
    while True:
        choice = main_menu()
        if choice in ["1", "2", "3"]:
            show_theory(choice)
        elif choice == "4":
            run_t_qnn_sim()
        elif choice == "5":
            run_confinement_model()
        elif choice == "6":
            show_references()
        elif choice == "0":
            print("\nCerrando sistema... ¡Buen día, Investigador!")
            time.sleep(1)
            break
        else:
            print("\n\033[1;31mOpción no válida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    start_dashboard()
