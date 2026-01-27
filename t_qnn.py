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
  - Metodología: Bayesiana con Distancia de Mahalanobis y Cosenos Directores

EQUIVALENCIA CONCEPTUAL:
  AWQPE phase estimation    ↔    T-QNN moment identification
  AWQPE ambiguity resolution ↔   T-QNN state recovery
  AWQPE reconstruction      ↔    T-QNN final classification
"""

import numpy as np
import tensorflow as tf
import tensorflow_probability as tfp
from typing import Tuple, List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from scipy.spatial.distance import mahalanobis
from sklearn.covariance import EmpiricalCovariance


# ============================================================================
# UTILIDADES ÁUREAS Y MATEMÁTICAS
# ============================================================================

def golden_ratio_operator(n: int, phi: float = 1.6180339887) -> Tuple[float, float]:
    """Calcula paridad y fase del operador áureo Ô_n para estabilización."""
    n_float = float(n)
    paridad = np.cos(np.pi * n_float)
    fase_mod = np.cos(np.pi * phi * n_float)
    return paridad, fase_mod


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
            (2 * np.pi * i) / self.num_moments
            for i in range(self.num_moments)
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
# MÓDULO: RESOLUCIÓN TOPOLÓGICA DE AMBIGÜEDAD (BAYES + MAHALANOBIS)
# ============================================================================

@dataclass
class TopologicalAmbiguityInfo:
    """Información de ambigüedad en contexto topológico con métricas avanzadas."""
    
    moment_id: int              # Momento detectado
    candidates: List[str]       # Estados candidatos dentro del momento
    probability_distribution: Dict[str, float]  # {estado: prob}
    top_candidates: List[Tuple[str, float]]   # [(estado, prob)]
    ambiguity_ratio: float      # Ratio entre top2/top1
    correlation_with_previous: Optional[float] = None  # Correlación con anterior
    confidence: float = 0.0     # Confianza general
    mahalanobis_distances: Optional[Dict[str, float]] = None # Distancias de Mahalanobis
    cosines: Optional[Tuple[float, float, float]] = None     # Cosenos directores (x,y,z)
    entropy: float = 0.0        # Entropía de Shannon del histograma


class TopologicalAmbiguityResolver:
    """Resuelve ambigüedad dentro de momentos usando estructura topológica y Bayes."""
    
    # Mapeo de momentos a estados permitidos en T-QNN
    # Nota: 1,6 (001, 110), 2,5 (010, 101), 3,4 (011, 100)
    MOMENT_TO_STATES = {
        0: ['001', '110'],    # Momento-1 (Estados 1 y 6)
        1: ['010', '101'],    # Momento-2 (Estados 2 y 5)
        2: ['011', '100'],    # Momento-3 (Estados 3 y 4)
    }
    
    def __init__(self):
        """Inicializar resolver con mapeo de momentos y estimador de covarianza."""
        self.transition_matrix = self._build_transition_matrix()
        self.covariance_estimator = EmpiricalCovariance()
        self.aureo_step = 1
    
    def _build_transition_matrix(self) -> np.ndarray:
        """
        Construir matriz de transición entre momentos.
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

    def _calculate_cosines(self, entropy: float, coherence: float) -> Tuple[float, float, float]:
        """Calcula los cosenos directores (x, y, z) para un vector de estado 3D."""
        epsilon = 1e-6
        entropy = max(entropy, epsilon)
        coherence = max(coherence, epsilon)
        magnitude = np.sqrt(entropy ** 2 + coherence ** 2 + 1)
        cos_x = entropy / magnitude
        cos_y = coherence / magnitude
        cos_z = 1 / magnitude
        return cos_x, cos_y, cos_z

    def _get_inverse_covariance(self, data: np.ndarray) -> np.ndarray:
        """Retorna la inversa de la matriz de covarianza de los datos."""
        if data.ndim != 2:
            data = data.reshape(-1, 1)
        self.covariance_estimator.fit(data)
        cov_matrix = self.covariance_estimator.covariance_
        try:
            inv_cov_matrix = np.linalg.inv(cov_matrix)
        except np.linalg.LinAlgError:
            inv_cov_matrix = np.linalg.pinv(cov_matrix)
        return inv_cov_matrix

    def _calculate_mahalanobis_distances(
        self,
        measurement_histogram: Dict[str, int],
        candidates: List[str]
    ) -> Dict[str, float]:
        """Calcula distancias de Mahalanobis para los candidatos permitidos."""
        # Generar datos sintéticos basados en el histograma para estimar la dispersión
        shots = []
        for state, count in measurement_histogram.items():
            val = int(state, 2)
            shots.extend([val] * count)

        if not shots:
            return {c: 10.0 for c in candidates}

        data = np.array(shots).reshape(-1, 1)
        inv_cov = self._get_inverse_covariance(data)
        mean_val = np.mean(data)

        distances = {}
        for cand in candidates:
            cand_val = int(cand, 2)
            diff = cand_val - mean_val
            # Distancia de Mahalanobis: sqrt( (x-mu)^T InvCov (x-mu) )
            d = np.sqrt(diff * inv_cov[0, 0] * diff)
            distances[cand] = float(d)

        return distances

    def _calculate_entropy(self, probabilities: List[float]) -> float:
        """Calcula la entropía de Shannon de una distribución."""
        probs = np.array(probabilities)
        probs = probs[probs > 0]
        if len(probs) == 0: return 0.0
        return -np.sum(probs * np.log2(probs))
    
    def resolve(
        self,
        moment_id: int,
        measurement_histogram: Dict[str, int],
        previous_moment: Optional[int] = None
    ) -> TopologicalAmbiguityInfo:
        """
        Resolver ambigüedad dentro del momento usando Bayes y Mahalanobis.
        
        Args:
            moment_id: Momento identificado
            measurement_histogram: Histograma de mediciones
            previous_moment: Momento anterior (para el prior de transición)
        
        Returns:
            TopologicalAmbiguityInfo con resolución avanzada
        """
        
        # Candidatos permitidos para este momento
        candidates = self.MOMENT_TO_STATES[moment_id]
        total_counts = sum(measurement_histogram.values())
        
        # 1. Likelihood basado en Mahalanobis
        mahal_dists = self._calculate_mahalanobis_distances(measurement_histogram, candidates)
        likelihoods = {s: np.exp(-mahal_dists[s]) for s in candidates}

        # 2. Prior Bayesiano
        # P(Momento) basado en la transición desde el momento anterior
        if previous_moment is not None:
            prior_transition = self.transition_matrix[previous_moment, moment_id]
        else:
            prior_transition = 1.0 / 3.0

        # 3. Posterior P(Estado | Medición)
        # Combinamos frecuencia observada, verosimilitud de Mahalanobis y prior de transición
        raw_probs = {}
        for s in candidates:
            freq = measurement_histogram.get(s, 0) / (total_counts + 1e-10)
            # Regla de Bayes simplificada
            raw_probs[s] = (freq + 1e-6) * likelihoods[s] * prior_transition

        # Normalización
        sum_probs = sum(raw_probs.values())
        prob_dist = {s: p / sum_probs for s, p in raw_probs.items()}

        # 4. Cálculo de Cosenos y Entropía
        entropy = self._calculate_entropy(list(prob_dist.values()))
        top_candidates = sorted(prob_dist.items(), key=lambda x: -x[1])
        
        # Coherencia estimada a partir de la dominancia del top candidato
        coherence = top_candidates[0][1] if top_candidates else 0.0
        cosines = self._calculate_cosines(entropy, coherence)

        # 5. Ratio de Ambigüedad y Confianza
        if len(top_candidates) >= 2:
            ambiguity_ratio = top_candidates[1][1] / (top_candidates[0][1] + 1e-10)
        else:
            ambiguity_ratio = 0.0
        
        # Confianza modulada por el coseno director Z (estabilidad)
        confidence = (1.0 - min(ambiguity_ratio, 1.0)) * cosines[2]
        
        correlation = self.transition_matrix[previous_moment, moment_id] if previous_moment is not None else None

        # Incrementar paso áureo
        self.aureo_step += 1
        
        return TopologicalAmbiguityInfo(
            moment_id=moment_id,
            candidates=candidates,
            probability_distribution=prob_dist,
            top_candidates=top_candidates,
            ambiguity_ratio=ambiguity_ratio,
            correlation_with_previous=correlation,
            confidence=float(confidence),
            mahalanobis_distances=mahal_dists,
            cosines=cosines,
            entropy=float(entropy)
        )
    
    def recover_likely_state(
        self,
        ambiguity_info: TopologicalAmbiguityInfo
    ) -> str:
        """
        Recuperar estado más probable dentro del momento.
        """
        if ambiguity_info.top_candidates:
            return ambiguity_info.top_candidates[0][0]
        else:
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
    Red neuronal cuántica topológica mejorada con AWQPE y Bayes/Mahalanobis.
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
        Simular fase estimada (AWQPE).
        """
        phase = np.sum(input_features * np.pi) / len(input_features)
        noise = np.random.normal(0, 0.1)
        noisy_phase = phase + noise
        return np.angle(np.exp(1j * noisy_phase))
    
    def generate_measurement_histogram(
        self,
        true_moment: int,
        shots: int = 1024
    ) -> Dict[str, int]:
        """
        Generar histograma de mediciones para un momento.
        """
        candidates = self.ambiguity_resolver.MOMENT_TO_STATES[true_moment]
        
        # Distribución sesgada
        if true_moment == 0:
            probs = [0.65, 0.35]
        elif true_moment == 1:
            probs = [0.6, 0.4]
        else:
            probs = [0.55, 0.45]
        
        state_choices = np.random.choice(candidates, size=shots, p=probs)
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
        Ejecutar medición completa de momento.
        """
        # 1. Simular fase
        phase_estimate = self.simulate_measurement(input_features)
        
        # 2. Mapear a momento
        moment_id, phase_distance = self.phase_mapper.phase_to_moment(phase_estimate)
        
        # 3. Generar histograma
        measurement_histogram = self.generate_measurement_histogram(moment_id, shots=shots)
        
        # 4. Resolver con Bayes + Mahalanobis
        previous_moment = self.moment_history[-1] if self.moment_history else None
        ambiguity_info = self.ambiguity_resolver.resolve(
            moment_id=moment_id,
            measurement_histogram=measurement_histogram,
            previous_moment=previous_moment
        )
        
        # 5. Recuperar estado
        likely_state = self.ambiguity_resolver.recover_likely_state(ambiguity_info)
        
        # 6. Confianza final combinada
        moment_clarity = 1.0 - phase_distance / np.pi
        final_confidence = (moment_clarity + ambiguity_info.confidence) / 2.0
        
        # Aplicar operador áureo para estabilización de confianza
        paridad, _ = golden_ratio_operator(self.ambiguity_resolver.aureo_step)
        if paridad < 0:
            final_confidence *= 0.95 # Penalización por paridad negativa

        self.moment_history.append(moment_id)
        
        return T_QNN_MeasurementResult(
            moment_id=moment_id,
            likely_state=likely_state,
            confidence=float(final_confidence),
            ambiguity_info=ambiguity_info
        )
    
    def classify(self, input_features: np.ndarray, shots: int = 1024) -> Tuple[int, str, float]:
        result = self.measure_moment(input_features, shots=shots)
        return result.moment_id, result.likely_state, result.confidence
    
    def generate_report(self, result: T_QNN_MeasurementResult) -> str:
        """Generar reporte detallado de la medición con métricas avanzadas."""
        report = "\n" + "="*70 + "\n"
        report += "T-QNN + AWQPE ADVANCED BAYESIAN REPORT\n"
        report += "="*70 + "\n\n"
        
        report += f"Momento identificado: {result.moment_id}\n"
        report += f"Estado probable: {result.likely_state}\n"
        report += f"Confianza Bayesiana: {result.confidence:.4f}\n\n"
        
        if result.ambiguity_info:
            info = result.ambiguity_info
            report += f"Distribución de Posterior Bayesiana:\n"
            for state, prob in info.probability_distribution.items():
                dist = info.mahalanobis_distances.get(state, 0)
                report += f"  {state}: {prob:.4f} (Dist. Mahalanobis: {dist:.4f})\n"
            
            report += f"\nEntropía del sistema: {info.entropy:.4f}\n"
            if info.cosines:
                cx, cy, cz = info.cosines
                report += f"Cosenos Directores (x, y, z): ({cx:.3f}, {cy:.3f}, {cz:.3f})\n"

            report += f"Ratio de ambigüedad: {info.ambiguity_ratio:.4f}\n"
        
        report += "\n" + "="*70 + "\n"
        return report


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def example_integration():
    """Demostración de T-QNN + AWQPE con la nueva metodología."""
    
    print("\n" + "#"*70)
    print("# T-QNN + AWQPE ADVANCED METHODOLOGY (BAYES + MAHALANOBIS)")
    print("#"*70 + "\n")
    
    qnn = TopologicalQNN_AWQPE()
    
    # Simular secuencia de momentos
    test_cases = [
        (np.array([0.5, 0.3, 0.2]), 0),
        (np.array([1.5, 1.3, 1.2]), 1),
        (np.array([2.5, 2.3, 2.2]), 2)
    ]
    
    for i, (features, t_mom) in enumerate(test_cases):
        print(f"TEST CASE {i+1}: Objetivo Momento {t_mom}")
        result = qnn.measure_moment(features, shots=1024)
        print(qnn.generate_report(result))


if __name__ == "__main__":
    example_integration()
