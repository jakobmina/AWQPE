"""
T-QNN + AWQPE INTEGRATION
═════════════════════════════════════════════════════════════════════════════

Implementación de Topological QNN mejorada con protocolo AWQPE
para resolución automática de ambigüedad y validación física.

CARACTERÍSTICAS:
  - T-QNN base: 6 estados permitidos, 3 momentos
  - AWQPE: Estimación adaptativa de momento
  - Integración: Resolución de ambigüedad + recuperación topológica
  - Validación: Coherencia física automática

EQUIVALENCIA CONCEPTUAL:
  AWQPE phase estimation    ↔    T-QNN moment identification
  AWQPE ambiguity resolution ↔   T-QNN state recovery
  AWQPE reconstruction      ↔    T-QNN final classification
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# INTEGRACIÓN: MAPEO DE CONCEPTOS
# ============================================================================

class PhaseToMomentMapper:
    """Mapea estimaciones de fase AWQPE a momentos T-QNN."""
    
    def __init__(self, num_moments: int = 3):
        """
        Args:
            num_moments: Número de momentos (3 para T-QNN base)
        """
        self.num_moments = num_moments
        
        # Fases asociadas a cada momento
        # Por convención: momento i está en la fase 2πi/num_moments
        self.moment_phases = [
            (2 * np.pi * i) / num_moments 
            for i in range(num_moments)
        ]
    
    def phase_to_moment(self, phase: float) -> Tuple[int, float]:
        """
        Mapear fase estimada al momento más cercano.
        
        Args:
            phase: Fase estimada (radianes, típicamente en [-π, π])
        
        Returns:
            (moment_id, distance): ID del momento y distancia a él
        """
        
        # Normalizar fase a [0, 2π]
        normalized_phase = np.mod(phase, 2 * np.pi)
        
        # Calcular distancias a cada momento
        distances = [
            abs(normalized_phase - mp)
            for mp in self.moment_phases
        ]
        
        # Momento más cercano
        moment_id = int(np.argmin(distances))
        distance = distances[moment_id]
        
        return moment_id, distance
    
    def phase_histogram_to_moment_histogram(
        self,
        phase_histogram: Dict[float, int]
    ) -> Dict[int, int]:
        """
        Convertir histograma de fases a histograma de momentos.
        
        Args:
            phase_histogram: {fase: count}
        
        Returns:
            {moment_id: count}
        """
        moment_histogram = {}
        
        for phase, count in phase_histogram.items():
            moment_id, _ = self.phase_to_moment(phase)
            moment_histogram[moment_id] = moment_histogram.get(moment_id, 0) + count
        
        return moment_histogram


# ============================================================================
# MÓDULO: RESOLUCIÓN TOPOLÓGICA DE AMBIGÜEDAD
# ============================================================================

@dataclass
class TopologicalAmbiguityInfo:
    """Información de ambigüedad en contexto topológico."""
    
    moment_id: int              # Momento detectado
    candidates: List[str]       # Estados candidatos dentro del momento
    probability_distribution: Dict[str, float]  # {estado: prob}
    top_candidates: List[Tuple[str, float]]   # [(estado, prob)]
    ambiguity_ratio: float      # Ratio entre top2/top1
    correlation_with_previous: Optional[float] = None  # Correlación con anterior
    confidence: float = 0.0     # Confianza general


class TopologicalAmbiguityResolver:
    """Resuelve ambigüedad dentro de momentos usando estructura topológica."""
    
    # Mapeo de momentos a estados permitidos en T-QNN
    MOMENT_TO_STATES = {
        0: ['001', '010'],    # Momento-1
        1: ['011', '100'],    # Momento-2
        2: ['101', '110'],    # Momento-3
    }
    
    def __init__(self):
        """Inicializar resolver con mapeo de momentos."""
        self.transition_matrix = self._build_transition_matrix()
    
    def _build_transition_matrix(self) -> np.ndarray:
        """
        Construir matriz de transición entre momentos.
        
        Basada en topología: P(M_i → M_j) depende de correlación.
        """
        n_moments = 3
        matrix = np.zeros((n_moments, n_moments))
        
        # Momento actual más probable en mismo momento
        for i in range(n_moments):
            matrix[i, i] = 0.7
        
        # Transiciones a momentos adyacentes
        for i in range(n_moments):
            adjacent = (i + 1) % n_moments
            matrix[i, adjacent] = 0.15
            
            prev = (i - 1) % n_moments
            matrix[i, prev] = 0.15
        
        return matrix
    
    def resolve(
        self,
        moment_id: int,
        measurement_histogram: Dict[str, int],
        previous_moment: Optional[int] = None
    ) -> TopologicalAmbiguityInfo:
        """
        Resolver ambigüedad dentro del momento.
        
        Args:
            moment_id: Momento identificado
            measurement_histogram: Histograma de mediciones
            previous_moment: Momento anterior (para correlación)
        
        Returns:
            TopologicalAmbiguityInfo con resolución
        """
        
        # Candidatos permitidos para este momento
        candidates = self.MOMENT_TO_STATES[moment_id]
        
        # Calcular distribución de probabilidad
        total_counts = sum(measurement_histogram.values())
        prob_dist = {
            state: measurement_histogram.get(state, 0) / total_counts
            for state in candidates
        }
        
        # Top candidatos
        top_candidates = sorted(
            prob_dist.items(),
            key=lambda x: -x[1]
        )
        
        # Ambiguity ratio (2do / 1ero)
        if len(top_candidates) >= 2:
            ambiguity_ratio = top_candidates[1][1] / (top_candidates[0][1] + 1e-10)
        else:
            ambiguity_ratio = 0.0
        
        # Confianza: invertido de ambiguity_ratio
        confidence = 1.0 - min(ambiguity_ratio, 1.0)
        
        # Correlación con momento anterior
        correlation = None
        if previous_moment is not None:
            correlation = self.transition_matrix[previous_moment, moment_id]
        
        return TopologicalAmbiguityInfo(
            moment_id=moment_id,
            candidates=candidates,
            probability_distribution=prob_dist,
            top_candidates=top_candidates,
            ambiguity_ratio=ambiguity_ratio,
            correlation_with_previous=correlation,
            confidence=confidence
        )
    
    def recover_likely_state(
        self,
        ambiguity_info: TopologicalAmbiguityInfo
    ) -> str:
        """
        Recuperar estado más probable dentro del momento.
        
        Args:
            ambiguity_info: Información de ambigüedad
        
        Returns:
            Estado más probable (ej: '011')
        """
        if ambiguity_info.top_candidates:
            return ambiguity_info.top_candidates[0][0]
        else:
            # Fallback: devolver primer candidato
            return ambiguity_info.candidates[0]


# ============================================================================
# MÓDULO: T-QNN MEJORADO CON AWQPE
# ============================================================================

@dataclass
class T_QNN_MeasurementResult:
    """Resultado de medición en T-QNN + AWQPE."""
    
    moment_id: int                      # Momento identificado (0, 1, 2)
    likely_state: str                   # Estado más probable ('001', '010', etc.)
    confidence: float                   # Confianza [0, 1]
    ambiguity_info: Optional[TopologicalAmbiguityInfo] = None


class TopologicalQNN_AWQPE:
    """
    Red neuronal cuántica topológica mejorada con AWQPE.
    
    Características:
    - 3 qubits de datos (6 estados permitidos)
    - 3 momentos identificables
    - Resolución automática de ambigüedad (topológica)
    - Validación de coherencia
    """
    
    def __init__(self, coherence_time: float = 1e-3):
        """
        Args:
            coherence_time: Tiempo de coherencia del sistema (segundos)
        """
        self.coherence_time = coherence_time
        
        # Mapeo fase → momento
        self.phase_mapper = PhaseToMomentMapper(num_moments=3)
        
        # Resolver de ambigüedad
        self.ambiguity_resolver = TopologicalAmbiguityResolver()
        
        # Historial de momentos (para correlación)
        self.moment_history: List[int] = []
    
    def simulate_measurement(
        self,
        input_features: np.ndarray
    ) -> np.ndarray:
        """
        Simular medición cuántica (fase estimada).
        
        Nota: En implementación real, esto vendría del protocolo AWQPE.
        Aquí simulamos para demostración.
        
        Args:
            input_features: Features de entrada (3 valores en [0, 2π])
        
        Returns:
            Fase estimada
        """
        # Sumar features ponderadas (simulación simplificada)
        phase = np.sum(input_features * np.pi) / len(input_features)
        
        # Agregar ruido gaussiano pequeño
        noise = np.random.normal(0, 0.1)
        noisy_phase = phase + noise
        
        # Normalizar a [-π, π]
        return np.angle(np.exp(1j * noisy_phase))
    
    def generate_measurement_histogram(
        self,
        true_moment: int,
        shots: int = 1024
    ) -> Dict[str, int]:
        """
        Generar histograma de mediciones para un momento.
        
        Args:
            true_moment: Momento verdadero (0, 1, 2)
            shots: Número de shots
        
        Returns:
            {estado: counts}
        """
        candidates = self.ambiguity_resolver.MOMENT_TO_STATES[true_moment]
        
        # Distribución sesgada hacia el estado "verdadero"
        if true_moment == 0:
            probs = [0.6, 0.4]  # Favorece '001'
        elif true_moment == 1:
            probs = [0.55, 0.45]  # Favorece '011' ligeramente
        else:  # true_moment == 2
            probs = [0.5, 0.5]  # Equiprobable
        
        # Muestrear
        state_choices = np.random.choice(
            candidates,
            size=shots,
            p=probs
        )
        
        # Contar
        histogram = {}
        for state in state_choices:
            histogram[state] = histogram.get(state, 0) + 1
        
        return histogram
    
    def measure_moment(
        self,
        input_features: np.ndarray,
        true_moment: Optional[int] = None,
        shots: int = 1024
    ) -> T_QNN_MeasurementResult:
        """
        Ejecutar medición completa de momento (con AWQPE logic).
        
        Args:
            input_features: Features de entrada
            true_moment: Momento verdadero (si se conoce, para simulación)
            shots: Número de shots cuánticos
        
        Returns:
            T_QNN_MeasurementResult con momento, estado, y confianza
        """
        
        # Paso 1: Simular fase estimada (simulación de AWQPE)
        phase_estimate = self.simulate_measurement(input_features)
        
        # Paso 2: Mapear fase a momento (Phase Estimation)
        moment_id, phase_distance = self.phase_mapper.phase_to_moment(phase_estimate)
        
        # Paso 3: Generar histograma de mediciones (Quantum Circuit Execution)
        measurement_histogram = self.generate_measurement_histogram(
            moment_id,
            shots=shots
        )
        
        # Paso 4: Resolver ambigüedad (Ambiguity Resolution)
        previous_moment = self.moment_history[-1] if self.moment_history else None
        
        ambiguity_info = self.ambiguity_resolver.resolve(
            moment_id=moment_id,
            measurement_histogram=measurement_histogram,
            previous_moment=previous_moment
        )
        
        # Paso 5: Recuperar estado probable (Topological Recovery)
        likely_state = self.ambiguity_resolver.recover_likely_state(ambiguity_info)
        
        # Paso 6: Calcular confianza final
        # Combina: momento clarity + state clarity + coherence
        moment_clarity = 1.0 - phase_distance / np.pi
        state_clarity = ambiguity_info.confidence
        
        final_confidence = (moment_clarity + state_clarity) / 2.0
        
        # Validar coherencia
        # Error esperado = 1 / (2^precision_bits)
        expected_error = 1.0 / (2**3)  # 3 qubits
        coherence_margin = self.coherence_time * expected_error
        
        if phase_distance > coherence_margin:
            final_confidence *= 0.9  # Penalizar si fase está lejos
        
        # Actualizar historial
        self.moment_history.append(moment_id)
        
        return T_QNN_MeasurementResult(
            moment_id=moment_id,
            likely_state=likely_state,
            confidence=final_confidence,
            ambiguity_info=ambiguity_info
        )
    
    def classify(
        self,
        input_features: np.ndarray,
        shots: int = 1024
    ) -> Tuple[int, str, float]:
        """
        Ejecutar clasificación completa (end-to-end).
        
        Args:
            input_features: Features de entrada
            shots: Shots cuánticos por medición
        
        Returns:
            (moment_id, likely_state, confidence)
        """
        result = self.measure_moment(input_features, shots=shots)
        return result.moment_id, result.likely_state, result.confidence
    
    def generate_report(self, result: T_QNN_MeasurementResult) -> str:
        """Generar reporte detallado de la medición."""
        report = "\n" + "="*70 + "\n"
        report += "T-QNN + AWQPE MEASUREMENT REPORT\n"
        report += "="*70 + "\n\n"
        
        report += f"Momento identificado: {result.moment_id}\n"
        report += f"Estado probable: {result.likely_state}\n"
        report += f"Confianza general: {result.confidence:.4f}\n\n"
        
        if result.ambiguity_info:
            info = result.ambiguity_info
            report += f"Candidatos en momento {result.moment_id}: {info.candidates}\n"
            report += f"Distribución de probabilidad:\n"
            for state, prob in info.probability_distribution.items():
                report += f"  {state}: {prob:.4f}\n"
            report += f"\nRatio de ambigüedad: {info.ambiguity_ratio:.4f}\n"
            
            if info.correlation_with_previous is not None:
                report += f"Correlación con momento anterior: {info.correlation_with_previous:.4f}\n"
        
        report += "\n" + "="*70 + "\n"
        return report


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def example_integration():
    """Demostración de T-QNN + AWQPE."""
    
    print("\n" + "#"*70)
    print("# T-QNN + AWQPE INTEGRATION EXAMPLE")
    print("#"*70 + "\n")
    
    # Crear QNN
    qnn = TopologicalQNN_AWQPE(coherence_time=1e-3)
    
    # Ejemplo 1: Medir momento 0
    print("EJEMPLO 1: Clasificación para Momento-0\n")
    
    input_features = np.array([0.5, 0.3, 0.2])  # Features de entrada
    result = qnn.measure_moment(input_features, true_moment=0, shots=1024)
    
    print(qnn.generate_report(result))
    
    # Ejemplo 2: Medir momento 1
    print("\nEJEMPLO 2: Clasificación para Momento-1\n")
    
    input_features = np.array([1.5, 1.3, 1.2])
    result = qnn.measure_moment(input_features, true_moment=1, shots=1024)
    
    print(qnn.generate_report(result))
    
    # Ejemplo 3: Medir momento 2
    print("\nEJEMPLO 3: Clasificación para Momento-2\n")
    
    input_features = np.array([2.5, 2.3, 2.2])
    result = qnn.measure_moment(input_features, true_moment=2, shots=1024)
    
    print(qnn.generate_report(result))
    
    # Batches: Múltiples clasificaciones
    print("\n" + "#"*70)
    print("# BATCH CLASSIFICATION: 10 Samples")
    print("#"*70 + "\n")
    
    qnn_reset = TopologicalQNN_AWQPE()
    
    results = []
    for i in range(10):
        # Feature aleatorio en [0, 2π]
        features = np.random.uniform(0, 2*np.pi, 3)
        moment, state, conf = qnn_reset.classify(features, shots=1024)
        results.append((moment, state, conf))
        print(f"Sample {i}: Moment={moment}, State={state}, Confidence={conf:.4f}")
    
    # Estadísticas
    moments = [r[0] for r in results]
    print(f"\nDistribución de momentos: {np.bincount(moments, minlength=3).tolist()}")
    print(f"Confianza promedio: {np.mean([r[2] for r in results]):.4f}")


if __name__ == "__main__":
    example_integration()
