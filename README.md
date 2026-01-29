 <html> <img align="center" width="250" height="250"  alt="awq2" src="https://github.com/user-attachments/assets/915b4910-0994-491b-8f58-7724cec97364" /> PROTOCOLO AWQPE - QuoreMind
 </html>

## ============================================
# AWQPE: Estimación Adaptativa de Fase Cuántica

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![GitHub last commit](https://img.shields.io/github/last-commit/jakobmina/AWQPE) ![GitHub license](https://img.shields.io/github/license/jakobmina/AWQPE) ![GitHub stars](https://img.shields.io/github/stars/jakobmina/AWQPE?style=social) ![GitHub forks](https://img.shields.io/github/forks/jakobmina/AWQPE?style=social) ![GitHub repo size](https://img.shields.io/github/repo-size/jakobmina/AWQPE) ![Estado](https://img.shields.io/badge/Estado-Terminado-green)

**Implementación profesional y rigurosa del protocolo AWQPE (Adaptive Windowed Quantum Phase Estimation), diseñada para estimación eficiente de fases cuánticas con reducido requerimiento de coherencia.**

## 📋 Descripción General

AWQPE es una mejora sustancial del algoritmo clásico de Estimación de Fase Cuántica (Quantum Phase Estimation, QPE) que direcciona una limitación crítica en computación cuántica: la profundidad de circuito requerida para alcanzar alta precisión.

### El Problema Fundamental

El algoritmo QPE estándar requiere controladores de fase unitaria de profundidad *exponencial* en bits de precisión. Para estimar una fase con precisión Δφ = 2^(-n), se necesitan compuertas de control con exponentes hasta 2^(n-1), lo que consume recursos de coherencia prohibitivamente altos en hardware cuántico actual.

### La Solución: Enfoque por Ventanas Adaptativas

AWQPE particiona la estimación en *ventanas de precisión acotada*, procesadas secuencialmente. Cada ventana opera con circuitos de profundidad constante—una estrategia análoga a cómo los microscopios adaptan campos de visión para revelar detalles a múltiples escalas sin perder enfoque global.

## 🎯 Características Principales

| Característica | Descripción |
|---|---|
| **Protocolo Completo** | Implementación de las 4 fases: Preparación, Ejecución, Resolución de Ambigüedad, Reconstrucción |
| **Validación Exhaustiva** | >350 tests unitarios e integración que aseguran corrección en cada paso |
| **Ejemplos Interactivos** | 6 casos de uso con operadores variados (fases simples, Berry, sensibilidad, personalizados) |
| **Arquitectura Extensible** | Sistema de herencia para operadores personalizados sin modificar núcleo |
| **Análisis de Error** | Métricas de confianza, validación estadística y física integradas |
| **Documentación Teórica** | Marcos rigurosos basados en literatura científica contemporánea |

## 🚀 Inicio Rápido

### Instalación

```bash
# Dependencias mínimas
pip install numpy

# Para testing (opcional)
pip install pytest
```

### Ejemplo Mínimo (2 minutos)

```python
from awqpe_protocol import AWQPEConfig, SimplePhaseOperator, AWQPEProtocol

# Configurar: 8 bits de precisión con ventanas de tamaño 3
config = AWQPEConfig(total_precision_bits=8, window_size=3)

# Definir operador con fase conocida (0.7 radianes)
operador = SimplePhaseOperator(phase=0.7)

# Ejecutar protocolo
protocolo = AWQPEProtocol(config, operador)
resultado = protocolo.run(verbose=False)

# Analizar resultado
print(f"Fase objetivo:      {0.7:.6f} rad")
print(f"Fase estimada:      {resultado.phase_estimate:.6f} rad")
print(f"Error absoluto:     {abs(0.7 - resultado.phase_estimate):.6f}")
print(f"Validación física:  {resultado.coherence_validated}")
```

### Ejecutar Ejemplos Interactivos

```bash
python examples.py
```

Sigue el menú interactivo para explorar diferentes operadores y configuraciones.

### Ejecutar Tests

```bash
# Suite completa (puede tomar 2-5 minutos)
pytest awqpe_tests.py -v

# Con cobertura
pytest awqpe_tests.py --cov=awqpe_protocol --cov-report=html
```

## 📚 Estructura del Repositorio

```
AWQPE/
├── awqpe_protocol.py              ⭐ NÚCLEO
│   ├── AWQPEConfig              Configuración de parámetros
│   ├── QuantumOperator          Clase base abstracta
│   ├── SimplePhaseOperator      Operador básico (tests)
│   ├── AWQPEProtocol            Implementación de 4 fases
│   └── AWQPEResult              Contenedor de resultados
│
├── awqpe_guia_completa.py         📚 DOCUMENTACIÓN
│   ├── Teoría fundamentada
│   ├── 6 ejemplos avanzados
│   ├── Guía de optimización
│   ├── Troubleshooting
│   └── Referencias científicas
│
├── awqpe_tests.py                 🧪 VALIDACIÓN
│   ├── Tests unitarios (>300)
│   ├── Tests integración
│   ├── Casos límite
│   ├── Validación estadística
│   └── Benchmarking
│
├── examples.py                    🔬 CASOS PRÁCTICOS
│   ├── Ejemplo 1: Fase simple
│   ├── Ejemplo 2: Fase de Berry
│   ├── Ejemplo 3: Análisis de sensibilidad
│   ├── Ejemplo 4: Múltiples fases
│   ├── Ejemplo 5: Análisis de error
│   └── Ejemplo 6: Operador personalizado
│
├── circuit_demonstration.py        Visualización de circuitos
├── confinamiento.py               Caso de uso: sistemas confinados
├── lattice_couple.py              Caso de uso: sistemas acoplados
├── metriplectic_committer.py      Caso de uso: dinámica metripléctica
│
└── README.md                      📖 ESTE ARCHIVO
```

## 🔧 Configuración de Parámetros

### Definiciones de Parámetros

| Parámetro | Rango Típico | Descripción |
|---|---|---|
| `total_precision_bits` | 4–16 | Bits totales de precisión: error = 2^(-n) |
| `window_size` | 2–5 | Bits procesados por ventana (define profundidad de circuito) |
| `n_shots` | 512–4096 | Repeticiones para estadística |
| `phase_kickback_depth` | 1–3 | Iteraciones de phase kickback por ventana |

### Configuraciones Recomendadas

#### Para Pruebas Rápidas
```python
config = AWQPEConfig(
    total_precision_bits=6,    # Error: 1/64 ≈ 1.5%
    window_size=2,              # Profundidad constante
    n_shots=512                 # Rápido
)
```

#### Balance Velocidad-Precisión
```python
config = AWQPEConfig(
    total_precision_bits=8,     # Error: 1/256 ≈ 0.4%
    window_size=3,              # Estándar
    n_shots=1024                # Recomendado
)
```

#### Máxima Precisión
```python
config = AWQPEConfig(
    total_precision_bits=12,    # Error: 1/4096 ≈ 0.025%
    window_size=4,              # Mayor demanda de coherencia
    n_shots=2048                # Estadística más robusta
)
```

## 🏗️ Arquitectura del Protocolo

### Las 4 Fases de AWQPE

```
┌─────────────────────────────────────────────────────┐
│ FASE I: PREPARACIÓN (Inicialización)                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Recibir operador unitario Û y parámetros       │
│  2. Particionar precisión en ventanas:              │
│     - Ventana 1: bits [0, w]                        │
│     - Ventana 2: bits [w, 2w]                       │
│     - ...                                           │
│  3. Asignar recursos por ventana                    │
│                                                      │
│  ✓ Valida: dimensiones, rangos de fase             │
│  ✓ Emite: reporte de configuración                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ FASE II: EJECUCIÓN (Por cada ventana)              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Para cada ventana j:                               │
│                                                      │
│  a) Inicializar qubits                              │
│  b) Preparar superposición de control               │
│  c) Aplicar Û^(2^k) para k ∈ [0, w-1]              │
│     → Phase kickback: control acumula fase          │
│  d) Aplicar iQFT (Quantum Fourier Transform inversa)│
│  e) Medir qubits de control                         │
│  f) Compilar histograma de resultados               │
│                                                      │
│  ✓ Valida: coherencia post-ejecución               │
│  ✓ Emite: distribución de probabilidad             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ FASE III: RESOLUCIÓN DE AMBIGÜEDAD                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Problema: cada ventana estima φ módulo 2π          │
│           (periódica, múltiples soluciones)         │
│                                                      │
│  Solución: usar solapamiento entre ventanas         │
│                                                      │
│  1. Identificar picos en histogramas                │
│  2. Calcular compatibilidad entre ventanas          │
│  3. Resolver ambigüedad mediante:                   │
│     - Continuidad de fase                           │
│     - Máxima verosimilitud                          │
│  4. Corregir bits si necesario                      │
│                                                      │
│  ✓ Valida: consistencia entre ventanas             │
│  ✓ Emite: bits corregidos de fase                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ FASE IV: RECONSTRUCCIÓN FINAL                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Concatenar bits de todas las ventanas:          │
│     b = [b₀b₁b₂...b_{n-1}]                          │
│                                                      │
│  2. Convertir a fase real:                          │
│     φ = 2π × (b / 2^n)                              │
│                                                      │
│  3. Validación física:                              │
│     - Verificar Û|ψ⟩ = e^(iφ)|ψ⟩                    │
│     - Comprobar coherencia entre ventanas           │
│     - Analizar confianza estadística                │
│                                                      │
│  ✓ Valida: fase reconstruida vs. esperada         │
│  ✓ Emite: resultado final con métricas             │
└─────────────────────────────────────────────────────┘
```

### Complejidad Computacional

| Aspecto | QPEA Estándar | AWQPE |
|---|---|---|
| Profundidad de Circuito | O(2^n) | **O(w)** ✓ |
| Número de Compuertas CNOT | O(2^n) | **O(n·w)** ✓ |
| Qubits Auxiliares | O(n) | **O(w)** ✓ |
| Shots Requeridos | O(2^(2n)) | **O(2^(2w))** ✓ |

Donde n = bits totales, w = tamaño de ventana.

## 🔬 Creando Operadores Personalizados

### Interfaz Base

Todos los operadores heredan de `QuantumOperator`:

```python
from awqpe_protocol import QuantumOperator
import numpy as np

class MiOperador(QuantumOperator):
    """Operador personalizado para mi caso de uso."""
    
    def __init__(self, parametro_1, parametro_2):
        """Inicializar con parámetros físicos."""
        self.param1 = parametro_1
        self.param2 = parametro_2
        self.matrix = self._construir_matriz()
        
    def _construir_matriz(self):
        """Retornar matriz 2x2 hermítica con eigenvalores conocidos."""
        # Implementar matriz U
        return matriz_unitaria
    
    def get_matrix(self):
        """Retornar representación matricial."""
        return self.matrix
    
    def get_expected_phase(self):
        """Retornar fase esperada (para validación)."""
        # Calcular autofase del eigenestado
        eigenvalores = np.linalg.eigvalsh(self.matrix)
        return np.angle(eigenvalores[0])  # o el de interés
    
    def describe(self):
        """Descripción legible del operador."""
        return f"MiOperador(param1={self.param1}, param2={self.param2})"
```

### Ejemplo: Operador de Pauli

```python
class PauliZOperator(QuantumOperator):
    """Operador σ_z con fase 0 (trivial, para diagnóstico)."""
    
    def __init__(self):
        self.matrix = np.array([[1, 0], [0, -1]], dtype=complex)
    
    def get_matrix(self):
        return self.matrix
    
    def get_expected_phase(self):
        return 0.0  # Eigenestado |0⟩ tiene fase 0
    
    def describe(self):
        return "Pauli Z Operator"
```

## 📊 Análisis de Resultados

### Estructura de AWQPEResult

```python
resultado.phase_estimate          # Fase estimada φ̂ ∈ [0, 2π)
resultado.phase_std               # Desviación estándar (±σ)
resultado.bits_reconstructed      # Bits finales [b₀, b₁, ..., b_{n-1}]
resultado.confidence_score        # Puntuación 0-1 (validación)
resultado.coherence_validated     # bool, ¿pasó validación de coherencia?
resultado.window_results          # Resultados por ventana
resultado.execution_time_seconds  # Tiempo total (heurístico)
```

### Interpretación de Confianza

```python
if resultado.confidence_score >= 0.95:
    print("✓ Excelente — Resulta muy confiable")
elif resultado.confidence_score >= 0.80:
    print("✓ Bueno — Confiable para aplicaciones estándar")
elif resultado.confidence_score >= 0.60:
    print("⚠ Aceptable — Requiere cautela, considerar repetir")
else:
    print("✗ Bajo — Resultados no confiables, revisar configuración")
```

## 🧪 Suite de Testing

### Ejecutar Tests Específicos

```bash
# Tests unitarios básicos
pytest awqpe_tests.py::test_config_validation -v

# Tests de operadores
pytest awqpe_tests.py -k "operator" -v

# Tests de fases integración
pytest awqpe_tests.py::test_phase_estimation -v

# Tests con cobertura
pytest awqpe_tests.py --cov=awqpe_protocol --cov-report=term-missing
```

### Estructura de Tests

- **Unitarios (~200)**: Validación de componentes individuales
- **Integración (~100)**: Flujos end-to-end
- **Límite (~30)**: Casos extremos
- **Estadísticos (~20)**: Validación probabil​ística

## 📖 Ruta de Aprendizaje Recomendada

### 👤 Para Principiantes (1-2 horas)

1. Leer sección "Descripción General" arriba
2. Ejecutar ejemplo mínimo
3. Revisar `ESTRUCTURA_AWQPE.md` (diagramas)
4. Ejecutar `examples.py` → Ejemplo 1 y 2
5. Inspeccionar `awqpe_protocol.py` (métodos principales)

### 👨‍💼 Para Usuarios Intermedios (3-4 horas)

1. Leer `awqpe_guia_completa.py` completa
2. Ejecutar todos los ejemplos en `examples.py`
3. Analizar `awqpe_tests.py` (casos de validación)
4. Crear un operador personalizado
5. Experimentar con variaciones de parámetros

### 👨‍🔬 Para Investigadores Avanzados (5+ horas)

1. Estudiar fundamentos matemáticos en `awqpe_guia_completa.py`
2. Analizar implementación detallada en `awqpe_protocol.py`
3. Ejecutar suite de tests completa con cobertura
4. Diseñar operadores especializados para su dominio
5. Integrar con hardware cuántico real (Qiskit/Cirq)
6. Contribuir mejoras (optimizaciones, nuevos operadores)

## 🎓 Conceptos Clave

### Estimación de Fase Cuántica

Dado un operador unitario Û con eigenestado |ψ⟩:
```
Û|ψ⟩ = e^(iφ)|ψ⟩
```
El objetivo es estimar la fase φ ∈ [0, 2π).

### Phase Kickback

En computación cuántica, aplicar un operador controlado U^(2^k) a un qubit de control en superposición resulta que el control "captura" la fase e^(i·2^k·φ):
```
(|0⟩ + |1⟩)/√2 ⊗ |ψ⟩  →  (|0⟩ + e^(i·2^k·φ)|1⟩)/√2 ⊗ |ψ⟩
```
Este mecanismo es el corazón de QPE.

### Transformada de Fourier Cuántica Inversa (iQFT)

Convierte amplitudes de fase en amplitudes de estado: si el registro acumula fase φ, la iQFT concentra probabilidad en el estado |⌊2^n · φ/(2π)⌋⟩.

### Resolución de Ambigüedad

Cada ventana estima φ módulo 2π (periódica). Al solapar ventanas y usar continuidad, se resuelve la ambigüedad global.

## ⚠️ Limitaciones y Consideraciones

1. **Simulación Clásica**: Implementación actual es simulación clásica (numpy). La arquitectura soporta backends cuánticos reales (Qiskit, Cirq) con adaptaciones menores.

2. **Ruido**: No simula ruido cuántico explícitamente. En hardware real, se requieren técnicas de mitigación.

3. **Escalabilidad**: Simulación clasica está limitada a ~15-20 qubits. Hardware real puede escalar a circuitos mayores.

4. **Eigenestados Preparados**: Se asume que |ψ⟩ es preparable eficientemente. Algunos operadores requieren preparación sofisticada.

## 🔗 Referencias Científicas

### Fundamentos Teóricos

- **Kitaev, A. Y.** (1995). "Quantum measurements and the Abelian Stabilizer Problem." *arXiv preprint quant-ph/9511026*.
- **Cleve, R., et al.** (1998). "Quantum algorithms revisited." *Proceedings of the Royal Society*.

### Optimizaciones Modernas

- **Berry, M. V.** (1984). "Quantal phase factors accompanying adiabatic changes." *Proceedings of the Royal Society A*.
- **Higgins, B. L., et al.** (2007). "Entanglement-enhanced measurement of a known phase." *Nature Physics*.

### Implementaciones Relacionadas

- [Qiskit Phase Estimation](https://qiskit.org/documentation/stubs/qiskit.algorithms.PhaseEstimation.html)
- [Cirq Phase Estimation](https://quantumai.google/reference/python/cirq/experiments)

## 🛠️ Troubleshooting

### P: El protocolo retorna confidence bajo (<0.6)

**R:** Común cuando:
- `window_size` demasiado pequeño → intentar aumentar a 3-4
- `n_shots` insuficiente → aumentar a 1024-2048
- Operador mal condicionado → revisar eigenvalores
- Fase esperada incorrecta → validar `get_expected_phase()`

### P: Error muy grande (>0.1 rad)

**R:** Revisar:
- `total_precision_bits` ¿es suficiente? (error ≈ π/2^n)
- ¿Fase esperada está en [0, 2π)?
- ¿`window_size` es compatible? (típicamente 2-4)

### P: Tiempo de ejecución muy largo

**R:**
- Reducir `total_precision_bits` (cada bit ≈ 2x shots)
- Reducir `n_shots` (pero afecta confianza)
- `window_size` óptimo suele ser 3

### P: "AttributeError: no se encuentra método"

**R:** Asegúrese que operador personalizado:
- Hereda de `QuantumOperator`
- Implementa `get_matrix()`, `get_expected_phase()`, `describe()`

## 📄 Licencia

MIT License — Libre para uso comercial y no comercial con atribución.

```
Copyright (c) 2026 jakobmina

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software...
```

## 🙋 Soporte y Contribuciones

### Reportar Issues

Incluya:
- Versión de Python (`python --version`)
- Versión de numpy (`pip show numpy`)
- Código mínimo reproducible (MCE)
- Salida de error completa

### Sugerir Mejoras

Areas abiertas para contribución:
- Soporte para frameworks cuánticos (Qiskit, Cirq)
- Simulación de ruido realista
- Optimizaciones de compilación
- Documentación adicional (español/inglés)
- Nuevos operadores especializados

## 📞 Contacto

- **Autor**: jakobmina
- **Repositorio**: https://github.com/jakobmina/AWQPE
- **Issues**: https://github.com/jakobmina/AWQPE/issues

---

## ✨ Próximos Pasos

1. **Comenzar AHORA**: `python examples.py`
2. **Aprender**: Leer `awqpe_guia_completa.py`
3. **Experimentar**: Modificar parámetros, crear operadores
4. **Integrar**: Usar en su proyecto de investigación
5. **Contribuir**: Compartir casos de uso, mejoras

---

**Última actualización**: Enero 2026  
**Versión**: 1.0.0  
**Estado**: ✅ Production Ready
