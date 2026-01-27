"""
================================================================================
GUÍA COMPLETA: PROTOCOLO AWQPE
Adaptive Windowed Quantum Phase Estimation
================================================================================

CONTENIDO:
1. Introducción teórica
2. Arquitectura del protocolo
3. Guía de uso básico
4. Ejemplos avanzados
5. Troubleshooting y optimización
================================================================================
"""

# ============================================================================
# 1. INTRODUCCIÓN TEÓRICA
# ============================================================================

"""
MARCO TEÓRICO:
==============

El Protocolo AWQPE (Adaptive Windowed Quantum Phase Estimation) es una mejora
del algoritmo estándar de estimación de fase cuántica (QPEA) que utiliza:

1. VENTANAS ADAPTATIVAS:
   - Divide la precisión total en bloques pequeños (ventanas)
   - Procesa bloques secuencialmente desde LSB a MSB
   - Reduce requisitos de coherencia respecto a QPEA tradicional

2. ESTIMACIÓN CON CORRECCIÓN DE ERRORES:
   - Detecta ambigüedades mediante ratio de probabilidades
   - Aplica correcciones LSB-to-MSB automáticamente
   - Maneja "Special Chunks" (casos de fase exacta 0.5)

3. VALIDACIÓN FÍSICA:
   - Verifica límites de coherencia del hardware
   - Normaliza resultados a rangos físicamente significativos
   - Proporciona métricas de confianza para cada bloque

COMPLEJIDAD:
- Qubits de control: O(m) donde m es tamaño de ventana
- Compuertas: O(2^m) por bloque
- Profundidad de circuito: O(m) (mejor que QPEA: O(n))
- Ventaja: Menor coherence requirement → ejecución más confiable


APLICACIONES:
=============

1. ESTIMACIÓN DE FASE DE BERRY:
   Calcular fase geométrica en sistemas cuánticos con simetría U(1)
   
2. SIMULACIÓN HAMILTONIANA:
   Estimar valores propios de Hamiltonianos en espectroscopia cuántica
   
3. DETECCIÓN DE MODOS TOPOLÓGICOS:
   Identificar características topológicas a través de fases geométricas
   
4. METROLOGÍA CUÁNTICA:
   Estimación precisa de parámetros con ventaja cuántica


REFERENCIAS MATEMÁTICAS:
========================

Ecuación fundamental:
  U |u⟩ = e^(2πiϕ) |u⟩

Fase de Berry (caso especial):
  ϕ_Berry = Ω/2
  donde Ω es el ángulo sólido subtendido por la trayectoria cerrada

Precisión alcanzable:
  Δϕ = 1/2^n
  donde n es el número total de bits de precisión

"""


# ============================================================================
# 2. ARQUITECTURA DEL PROTOCOLO
# ============================================================================

"""
ESTRUCTURA EN FASES:

┌─────────────────────────────────────────────────────────────────────┐
│                    FASE I: PREPARACIÓN (SETUP)                       │
├─────────────────────────────────────────────────────────────────────┤
│ I.1 Definición del Sistema                                           │
│     └─ Verificar: U|u⟩ = e^(2πiϕ)|u⟩                               │
│                                                                       │
│ I.2 Estrategia de Ventanas                                           │
│     └─ Dividir n bits en bloques de tamaño m                         │
│     └─ Cantidad de ventanas: ⌈n/m⌉                                   │
│                                                                       │
│ I.3 Asignación de Recursos                                           │
│     └─ Control qubits: m per ventana                                 │
│     └─ Target qubits: tamaño del autoestado                          │
│     └─ Total N_shots: repeticiones de medición                       │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   FASE II: EJECUCIÓN (POR BLOQUE)                    │
├─────────────────────────────────────────────────────────────────────┤
│ Para cada bloque i (LSB → MSB):                                      │
│                                                                       │
│ II.1 Inicialización                                                   │
│      ├─ Preparar qubits de control en |0⟩                            │
│      └─ Aplicar Hadamard: |0⟩ → (|0⟩ + |1⟩)/√2                      │
│                                                                       │
│ II.2 Phase Kickback                                                   │
│      ├─ Aplicar U^(2^k) controlada, k = 0,1,...,m-1                │
│      └─ La fase se codifica en amplitud de qubits de control         │
│                                                                       │
│ II.3 Transformada de Fourier Inversa (IQFT)                         │
│      └─ Convertir amplitudes (fase) a estados de base computacional  │
│                                                                       │
│ II.4 Medición                                                         │
│      ├─ Ejecutar circuito N_shots veces                              │
│      └─ Construir histograma de resultados                           │
│                                                                       │
│ → BlockResult con histogram, top_candidates, ambiguity_ratio         │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│            FASE III: RESOLUCIÓN DE AMBIGÜEDAD (POST-PROC)            │
├─────────────────────────────────────────────────────────────────────┤
│ III.1 Identificación de Candidatos                                   │
│       └─ Extraer dos resultados más probables (t₁*, t₂*)             │
│                                                                       │
│ III.2 Cálculo de Ratio                                               │
│       └─ ρ = P(t₂*) / P(t₁*)                                         │
│       └─ Si ρ > ϵ (umbral): hay ambigüedad                           │
│                                                                       │
│ III.3 Corrección LSB-to-MSB                                          │
│       ├─ Usar MSB del bloque actual para corrección anterior         │
│       ├─ Caso especial: si fase = 0.5, ajuste adaptativo            │
│       └─ Propagación correcta de bits desde LSB a MSB                │
│                                                                       │
│ → Bits corregidos para cada bloque                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  FASE IV: RECONSTRUCCIÓN FINAL                       │
├─────────────────────────────────────────────────────────────────────┤
│ IV.1 Concatenación                                                    │
│      └─ Unir bits: [LSB bits] + [MSB bits]                           │
│      └─ Generar cadena binaria completa                              │
│                                                                       │
│ IV.2 Conversión a Fase                                               │
│      ├─ ϕ_est = (valor decimal) / 2^n                                │
│      ├─ Convertir a radianes: ϕ_rad = ϕ_est × 2π                    │
│      └─ Normalizar a [-π, π]                                         │
│                                                                       │
│ IV.3 Validación Física                                               │
│      ├─ Verificar rango de coherencia                                │
│      ├─ Calcular error total acumulado                               │
│      └─ Generar métricas de confianza                                │
│                                                                       │
│ → PhaseEstimationResult con ϕ_est final                              │
└─────────────────────────────────────────────────────────────────────┘

FLUJO DE DATOS:
===============

   Operador U → SetupPhase → QuantumCircuitExecution
                                      ↓
                            BlockResult (×num_windows)
                                      ↓
                          AmbiguityResolution
                                      ↓
                            Corrected Bits (×num_windows)
                                      ↓
                         FinalReconstruction
                                      ↓
                          PhaseEstimationResult

"""


# ============================================================================
# 3. GUÍA DE USO BÁSICO
# ============================================================================

"""
PASO 1: IMPORTAR Y CONFIGURAR
=============================

from awqpe_protocol import (
    AWQPEConfig,
    SimplePhaseOperator,
    AWQPEProtocol
)

# Crear configuración
config = AWQPEConfig(
    total_precision_bits=8,      # Precisión total en bits
    window_size=3,               # Tamaño de cada ventana
    n_shots=1024,                # Mediciones por bloque
    ambiguity_threshold=0.9      # Umbral para detectar ambigüedad
)


PASO 2: DEFINIR OPERADOR
========================

# Opción A: Fase simple (para pruebas)
target_phase = 0.7  # radianes
operator = SimplePhaseOperator(target_phase)

# Opción B: Fase de Berry
from awqpe_protocol import BerryCurvatureOperator
solid_angle = 2.5  # estereorradianes
operator = BerryCurvatureOperator(solid_angle)

# Opción C: Operador personalizado
class MyCustomOperator(QuantumOperator):
    def apply(self, eigenstate, power):
        # Tu lógica aquí
        phase = ...
        return eigenstate, phase
    
    def get_eigenstate(self):
        return np.array([...])
    
    @property
    def name(self):
        return "MyCustomOperator"


PASO 3: EJECUTAR PROTOCOLO
==========================

protocol = AWQPEProtocol(config, operator)
result = protocol.run(verbose=True)

# verbose=True: imprime reportes detallados
# verbose=False: solo retorna resultado


PASO 4: ANALIZAR RESULTADO
==========================

print(f"Fase estimada: {result.phase_estimate:.6f} rad")
print(f"Fase en grados: {np.degrees(result.phase_estimate):.2f}°")
print(f"Error total: {result.total_error:.2e}")
print(f"Validación física: {result.coherence_validated}")

# Acceder a resultados por bloque
for br in result.block_results:
    print(f"Bloque {br.block_index}: {br.phase_bits}")
    print(f"  Confianza: {br.confidence:.4f}")
    print(f"  Ambigüedad: {br.ambiguity_ratio:.4f}")


CONFIGURACIÓN RECOMENDADA:
==========================

Para MÁXIMA PRECISIÓN (tolerancia de error < 0.001):
  - total_precision_bits: 12-16
  - window_size: 4-5
  - n_shots: 2048-4096
  - ambiguity_threshold: 0.85

Para BALANCE VELOCIDAD-PRECISIÓN (tolerancia 0.01):
  - total_precision_bits: 8-10
  - window_size: 3-4
  - n_shots: 1024
  - ambiguity_threshold: 0.90

Para PRUEBAS RÁPIDAS (tolerancia 0.1):
  - total_precision_bits: 6-8
  - window_size: 2-3
  - n_shots: 512
  - ambiguity_threshold: 0.95

"""


# ============================================================================
# 4. EJEMPLOS AVANZADOS
# ============================================================================

"""
EJEMPLO 1: COMPARAR MÚLTIPLES FASES
===================================

from awqpe_protocol import AWQPEConfig, SimplePhaseOperator, AWQPEProtocol
import numpy as np
import matplotlib.pyplot as plt

config = AWQPEConfig(total_precision_bits=10, window_size=4, n_shots=2048)

target_phases = np.linspace(0, 2*np.pi, 8)
results = []

for target_phase in target_phases:
    operator = SimplePhaseOperator(target_phase)
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=False)
    results.append((target_phase, result.phase_estimate, result.total_error))

# Visualizar
targets, estimates, errors = zip(*results)
plt.figure(figsize=(10, 6))
plt.plot(targets, targets, 'k--', label='Ideal', alpha=0.5)
plt.errorbar(targets, estimates, yerr=errors, fmt='o', label='AWQPE', capsize=5)
plt.xlabel('Target Phase (rad)')
plt.ylabel('Estimated Phase (rad)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()


EJEMPLO 2: ANÁLISIS DE SENSIBILIDAD A PARÁMETROS
=================================================

config_variations = [
    {"total_precision_bits": 8, "window_size": 2},
    {"total_precision_bits": 8, "window_size": 3},
    {"total_precision_bits": 8, "window_size": 4},
]

target_phase = 0.7

for config_dict in config_variations:
    config = AWQPEConfig(**config_dict)
    operator = SimplePhaseOperator(target_phase)
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=False)
    
    print(f"Config {config_dict}:")
    print(f"  Error: {result.total_error:.2e}")
    print(f"  Tiempo (simulado): {len(result.block_results)} bloques")
    print()


EJEMPLO 3: ESTIMACIÓN CON RUIDO SIMULADO
=========================================

class NoisyPhaseOperator(SimplePhaseOperator):
    '''Operador que simula ruido en la medición'''
    
    def __init__(self, target_phase, noise_level=0.01):
        super().__init__(target_phase)
        self.noise_level = noise_level
    
    def apply(self, eigenstate, power):
        state, phase = super().apply(eigenstate, power)
        # Añadir ruido gaussiano
        noisy_phase = phase + np.random.normal(0, self.noise_level)
        return state, noisy_phase

# Comparar sin ruido vs con ruido
target_phase = 0.7
config = AWQPEConfig(total_precision_bits=10, window_size=4, n_shots=2048)

operator_clean = SimplePhaseOperator(target_phase)
protocol_clean = AWQPEProtocol(config, operator_clean)
result_clean = protocol_clean.run(verbose=False)

operator_noisy = NoisyPhaseOperator(target_phase, noise_level=0.05)
protocol_noisy = AWQPEProtocol(config, operator_noisy)
result_noisy = protocol_noisy.run(verbose=False)

print(f"Fase objetivo: {target_phase:.6f}")
print(f"Estimación limpia: {result_clean.phase_estimate:.6f} (error: {abs(target_phase - result_clean.phase_estimate):.6f})")
print(f"Estimación con ruido: {result_noisy.phase_estimate:.6f} (error: {abs(target_phase - result_noisy.phase_estimate):.6f})")


EJEMPLO 4: VALIDACIÓN CONTRA VALORES TEÓRICOS
==============================================

from awqpe_protocol import AWQPEConfig, BerryCurvatureOperator, AWQPEProtocol

# Calcular fase de Berry para diferentes ángulos sólidos
solid_angles = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
config = AWQPEConfig(total_precision_bits=12, window_size=4, n_shots=2048)

for solid_angle in solid_angles:
    theoretical_phase = solid_angle / 2.0
    
    operator = BerryCurvatureOperator(solid_angle)
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=False)
    
    error = abs(theoretical_phase - result.phase_estimate)
    rel_error = error / theoretical_phase * 100
    
    print(f"Ω = {solid_angle:.1f} sr: teórico={theoretical_phase:.6f}, "
          f"estimado={result.phase_estimate:.6f}, "
          f"error={rel_error:.2f}%")

"""


# ============================================================================
# 5. TROUBLESHOOTING Y OPTIMIZACIÓN
# ============================================================================

"""
PROBLEMA 1: RATIO DE AMBIGÜEDAD MUY ALTO
==========================================

Síntoma: ambiguity_ratio > 0.95 constantemente
Causa: Distribución de probabilidad muy plana

Soluciones:
1. Aumentar n_shots (1024 → 2048 o 4096)
2. Reducir window_size (3 → 2)
3. Aumentar total_precision_bits
4. Revisar que el operador U esté bien implementado

Ejemplo:
  config = AWQPEConfig(
      total_precision_bits=10,
      window_size=2,      # ← reducido
      n_shots=4096,       # ← aumentado
      ambiguity_threshold=0.85
  )


PROBLEMA 2: ERROR TOTAL DEMASIADO GRANDE
=========================================

Síntoma: total_error > 1e-2, pero esperábamos mejor

Causa: Errores acumulativos en múltiples bloques

Soluciones:
1. Aumentar total_precision_bits (8 → 12)
2. Optimizar correcciones LSB-to-MSB
3. Verificar límites de coherencia
4. Reducir ambiguity_threshold para ser más selectivo

Diagnóstico:
  for br in result.block_results:
      if br.ambiguity_ratio > 0.9:
          print(f"Bloque {br.block_index} con alta ambigüedad")


PROBLEMA 3: COHERENCE VALIDATED = FALSE
========================================

Síntoma: coherence_validated es False en resultado

Causa: Error estimado exceede tiempo de coherencia del hardware

Soluciones:
1. Reducir total_precision_bits
2. Aumentar coherence_time en configuración (si es posible)
3. Usar hardware con mayor tiempo de coherencia
4. Considerar técnicas de error correction

Diagnóstico:
  error_allowed = config.coherence_time / (2**config.total_precision_bits)
  actual_error = result.total_error
  print(f"Error permitido: {error_allowed:.2e}")
  print(f"Error actual: {actual_error:.2e}")


OPTIMIZACIÓN 1: PARA VELOCIDAD DE EJECUCIÓN
===========================================

config = AWQPEConfig(
    total_precision_bits=6,      # Menos bits
    window_size=2,               # Ventanas pequeñas
    n_shots=512,                 # Menos mediciones
    ambiguity_threshold=0.95     # Más tolerante
)

# Resultado: ejecución 4x más rápida, precisión ~0.1


OPTIMIZACIÓN 2: PARA MÁXIMA PRECISIÓN
======================================

config = AWQPEConfig(
    total_precision_bits=16,     # Muchos bits
    window_size=5,               # Ventanas grandes
    n_shots=4096,                # Muchas mediciones
    ambiguity_threshold=0.80,    # Selectivo
    validate_physics=True
)

# Resultado: precisión < 1e-4, pero tiempo ~10x mayor


OPTIMIZACIÓN 3: BALANCE AUTOMÁTICO
===================================

def find_optimal_config(target_error, max_coherence_time):
    '''Encontrar configuración óptima automáticamente'''
    for bits in range(6, 16):
        for window in range(2, min(bits, 5)):
            config = AWQPEConfig(
                total_precision_bits=bits,
                window_size=window,
                coherence_time=max_coherence_time
            )
            
            operator = SimplePhaseOperator(0.5)
            protocol = AWQPEProtocol(config, operator)
            result = protocol.run(verbose=False)
            
            if result.total_error <= target_error:
                return config, result
    
    raise ValueError("No se pudo encontrar configuración válida")


PROFILING Y DIAGNÓSTICO
=======================

from awqpe_protocol import AWQPEProtocol
import time

protocol = AWQPEProtocol(config, operator)

# Medir tiempo por fase
start = time.time()
result = protocol.run(verbose=False)
total_time = time.time() - start

# Análisis detallado
print(f"Tiempo total: {total_time:.3f}s")
print(f"Número de bloques: {len(result.block_results)}")
print(f"Tiempo promedio por bloque: {total_time / len(result.block_results):.3f}s")
print(f"Error total: {result.total_error:.2e}")
print(f"Coherencia validada: {result.coherence_validated}")

# Identificar bloques problemáticos
for br in result.block_results:
    if br.ambiguity_ratio > config.ambiguity_threshold:
        print(f"⚠️  Bloque {br.block_index}: ambigüedad = {br.ambiguity_ratio:.4f}")

"""


# ============================================================================
# REFERENCIAS Y LECTURA ADICIONAL
# ============================================================================

"""
PAPERS CIENTÍFICOS RELEVANTES:
==============================

[1] Kitaev, A. Y. (1995)
    "Quantum measurements and the Abelian Stabilizer Problem"
    https://arxiv.org/abs/quant-ph/9511026

[2] Berry, M. V. (1984)
    "Quantal phase factors accompanying adiabatic changes"
    Proceedings of the Royal Society A: Mathematical, Physical and Engineering Sciences

[3] Cleve, R., Ekert, A., Macchiavello, C., & Mosca, M. (1998)
    "Quantum algorithms revisited"
    https://arxiv.org/abs/quant-ph/9801070

[4] Montanaro, A. (2016)
    "Quantum algorithms: an overview"
    npj Quantum Information


RECURSOS EN LÍNEA:
=================

- IBM Quantum Learning: https://learning.quantum.ibm.com/
- Qiskit Documentation: https://qiskit.org/documentation/
- MIT OpenCourseWare: Quantum Computing
- Stanford CS 269Q: Quantum Computing


IMPLEMENTACIONES DE REFERENCIA:
==============================

- Qiskit: https://github.com/Qiskit/qiskit
- Cirq (Google): https://github.com/quantumlib/Cirq
- PennyLane: https://github.com/PennyLaneAI/pennylane
- ProjectQ: https://github.com/ProjectQ-Framework/ProjectQ

"""

print(__doc__)
