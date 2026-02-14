"""
================================================================================
AWQPE PROTOCOL CORE
================================================================================

Implementación rigurosa del protocolo de cómputo de fase cuántica adaptativo
basado en ventanas, con énfasis en la resolución de ambigüedad y corrección
de errores LSB-to-MSB.

Autor: Quantum Computing Research
Referencia: Adaptación de QPEA con correcciones geometría de fases cuánticas
================================================================================
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional
from enum import Enum

from .operators import (
    QuantumOperator,
    SimplePhaseOperator,
    BerryCurvatureOperator,
    MetriplecticCircuitOperator
)


# ============================================================================
# CONFIGURACIÓN Y TIPOS
# ============================================================================

class PhaseEstimationError(Exception):
    """Excepción base para errores en la estimación de fase."""
    pass


class AmbiguityResolutionError(PhaseEstimationError):
    """Error en la resolución de ambigüedad entre candidatos."""
    pass


@dataclass
class AWQPEConfig:
    """Configuración del protocolo AWQPE."""
    
    # Parámetros de precisión
    total_precision_bits: int = 8  # n bits totales
    window_size: int = 3            # mi bits por ventana
    n_shots: int = 1024             # Nshots mediciones por bloque
    
    # Parámetros de resolución de ambigüedad
    ambiguity_threshold: float = 0.9  # ϵ umbral para ratio
    coherence_time: float = 1e-3      # Tiempo de coherencia (segundos)
    
    # Validación física y Metriplectic Reset
    validate_physics: bool = True
    max_phase_range: Tuple[float, float] = (-np.pi, 7.0)
    phase_reset_value: float = 7.0    # Umbral de reinicio (Default: Metriplectic 7.0)
    
    def __post_init__(self):
        """Validar parámetros de configuración."""
        if self.total_precision_bits <= 0:
            raise ValueError("total_precision_bits debe ser positivo")
        if self.window_size <= 0 or self.window_size > self.total_precision_bits:
            raise ValueError(f"window_size debe estar entre 1 y {self.total_precision_bits}")
        if not (0 < self.ambiguity_threshold < 1):
            raise ValueError("ambiguity_threshold debe estar entre 0 y 1")
    
    @property
    def num_windows(self) -> int:
        """
        Número de ventanas con solapamiento de 1 bit.
        """
        if self.total_precision_bits <= self.window_size:
            return 1
            
        effective_bits = self.window_size - 1
        # k >= (T-S)/(S-1)
        k_max = int(np.ceil((self.total_precision_bits - self.window_size) / effective_bits))
        return k_max + 1

    @property
    def control_qubits_per_window(self) -> int:
        """Número de qubits de control por ventana."""
        return self.window_size


@dataclass
class BlockResult:
    """Resultado de procesamiento de un bloque."""
    
    block_index: int
    window_size: int
    measurement_histogram: Dict[int, int]
    top_candidates: List[Tuple[int, float]]  # [(valor, probabilidad), ...]
    phase_bits: str
    ambiguity_ratio: float
    required_correction: Optional[int] = None
    confidence: float = 0.0


@dataclass
class PhaseEstimationResult:
    """Resultado final de estimación de fase."""
    
    phase_estimate: float           # ϕest estimada
    phase_bits: str                 # Representación binaria
    block_results: List[BlockResult]
    total_error: float
    physical_quantity: Optional[float] = None
    coherence_validated: bool = True
    
    def __str__(self) -> str:
        """Representación legible del resultado."""
        return (
            f"Phase Estimate: {self.phase_estimate:.6f}\n"
            f"Phase Bits: {self.phase_bits}\n"
            f"Total Error: {self.total_error:.2e}\n"
            f"Physical Quantity: {self.physical_quantity}\n"
            f"Coherence Valid: {self.coherence_validated}"
        )


# ============================================================================
# MÓDULO I: FASE DE PREPARACIÓN
# ============================================================================

class SetupPhase:
    """Encapsula la Fase de Preparación (Setup) del protocolo AWQPE."""
    
    def __init__(self, config: AWQPEConfig, operator: QuantumOperator):
        """
        Args:
            config: Configuración del protocolo
            operator: Operador unitario U con autoestado |u⟩
        """
        self.config = config
        self.operator = operator
        self.eigenstate = operator.get_eigenstate()
        
        # Validar que el operador tiene autoestado válido
        if not self._is_valid_eigenstate():
            raise ValueError("El operador no proporciona un autoestado válido")
    
    def _is_valid_eigenstate(self) -> bool:
        """Verificar que el autoestado es normalizado."""
        norm = np.linalg.norm(self.eigenstate)
        return np.isclose(norm, 1.0)
    
    def define_system(self) -> Dict:
        """
        I.1 Definición del Sistema: Verificar U|u⟩ = e^(2πiϕ)|u⟩
        
        Returns:
            Diccionario con información del sistema
        """
        return {
            "operator": self.operator.name,
            "eigenstate_norm": np.linalg.norm(self.eigenstate),
            "eigenstate_valid": self._is_valid_eigenstate(),
        }
    
    def strategy_windows(self) -> Dict:
        """
        I.2 Estrategia de Ventanas: Dividir precisión en bloques.
        
        Returns:
            Diccionario describiendo la estrategia de ventanas
        """
        num_windows = self.config.num_windows
        control_qubits = self.config.control_qubits_per_window
        
        windows = []
        for i in range(num_windows):
            start_bit = i * control_qubits
            end_bit = min((i + 1) * control_qubits, self.config.total_precision_bits)
            actual_size = end_bit - start_bit
            
            windows.append({
                "window_index": i,
                "bit_range": (start_bit, end_bit),
                "actual_size": actual_size,
                "power_range": list(range(actual_size))
            })
        
        return {
            "total_precision_bits": self.config.total_precision_bits,
            "window_size": control_qubits,
            "num_windows": num_windows,
            "windows": windows
        }
    
    def resource_allocation(self) -> Dict:
        """
        I.3 Recursos de Hardware: Reservar qubits necesarios.
        
        Returns:
            Diccionario con asignación de recursos
        """
        control_qubits = self.config.control_qubits_per_window
        target_qubits = len(self.eigenstate)
        
        return {
            "control_qubits_per_window": control_qubits,
            "target_qubits": target_qubits,
            "total_qubits_per_window": control_qubits + target_qubits,
            "num_windows": self.config.num_windows,
            "total_qubits_allocated": (control_qubits + target_qubits) * self.config.num_windows,
            "n_shots": self.config.n_shots
        }
    
    def generate_report(self) -> str:
        """Generar reporte completo de preparación."""
        report = "=" * 70 + "\n"
        report += "FASE DE PREPARACIÓN (SETUP) - AWQPE\n"
        report += "=" * 70 + "\n\n"
        
        system = self.define_system()
        report += "I.1 Definición del Sistema:\n"
        for key, value in system.items():
            report += f"  {key}: {value}\n"
        report += "\n"
        
        windows = self.strategy_windows()
        report += "I.2 Estrategia de Ventanas:\n"
        report += f"  Total bits de precisión: {windows['total_precision_bits']}\n"
        report += f"  Tamaño de ventana: {windows['window_size']}\n"
        report += f"  Número de ventanas: {windows['num_windows']}\n"
        report += "\n"
        
        resources = self.resource_allocation()
        report += "I.3 Asignación de Recursos:\n"
        for key, value in resources.items():
            report += f"  {key}: {value}\n"
        
        return report


# ============================================================================
# MÓDULO II: EJECUCIÓN DEL CIRCUITO CUÁNTICO
# ============================================================================

class QuantumCircuitExecution:
    """
    MODIFICACIÓN SUGERIDA PARA QBRAID:
    Se podría añadir un parámetro 'backend' en __init__ para pasarle
    un backend de Qiskit/Qbraid. Las funciones como 'simulate_qpe_distribution'
    y 'measure_and_collapse' serían reemplazadas por una única función que
    construya y ejecute un circuito de Qiskit.
    """
    """Encapsula la Fase de Ejecución del protocolo AWQPE."""
    
    def __init__(self, config: AWQPEConfig, operator: QuantumOperator):
        """
        Args:
            config: Configuración del protocolo
            operator: Operador unitario U
        """
        self.config = config
        self.operator = operator
        self.results: List[BlockResult] = []
    
    def initialize_qubits(self) -> Dict:
        """
        II.1 Inicialización: Colocar qubits de control en superposición.
        
        Returns:
            Estado de qubits de control
        """
        # Simulación: qubits en estado |+⟩ después de Hadamard
        control_state = np.ones(2 ** self.config.window_size) / np.sqrt(2 ** self.config.window_size)
        
        return {
            "control_state": control_state,
            "superposition_valid": np.isclose(np.linalg.norm(control_state), 1.0)
        }
    
    def phase_kickback(self, block_index: int) -> Tuple[float, int]:
        """
        II.2 Transferencia de Fase (Phase Kickback): Aplicar U^(2^k).
        
        Calcula la fase acumulada teórica para el bloque actual basada en 
        las potencias U^(2^{offset+j}).
        
        Args:
            block_index: Índice del bloque actual
        
        Returns:
            Tupla (fase_objetivo_bloque, n_qubits_ventana)
        """
        window_size = self.config.window_size
        control_qubits = self.config.control_qubits_per_window
        
        # Calcular offset de bits para este bloque (solapamiento de 1 bit)
        bit_offset = block_index * (control_qubits - 1)
        
        # Determinar cuántos bits reales tiene este bloque
        num_new_bits = control_qubits - 1
        actual_bits = min(control_qubits, self.config.total_precision_bits - bit_offset)
        
        # Extraer fase del operador
        eigenstate = self.operator.get_eigenstate()
        _, phase_u = self.operator.apply(eigenstate, 0) # Fase de U^1 (2^0)
        
        # La fase efectiva para este bloque es (phase_u * 2^bit_offset)
        # En QPE, esto se mapea a bits binarios en el registro de la ventana
        return phase_u, actual_bits, bit_offset
    
    def simulate_qpe_distribution(self, phase_u: float, m_bits: int, offset: int) -> Dict[int, float]:
        """
        II.3 & II.4 Simulación de IQFT y Medición (Modelo Probabilístico).
        
        Utiliza la fórmula teórica de QPE para la probabilidad de medir el estado |y>:
        P(y) = |1/N * sum_{j=0}^{N-1} exp(2πi * (2^offset * φ * N - y) * j / N)|^2
        donde φ = phase_u / phase_reset_value y N = 2^m_bits.
        
        Args:
            phase_u: Fase base del operador U
            m_bits: Número de qubits en la ventana
            offset: Exponente de desplazamiento
            
        Returns:
            Diccionario de probabilidades {estado_binario: probabilidad}
        """
        if m_bits <= 0:
            return {0: 1.0}
            
        N = int(round(2 ** m_bits))
        if N <= 0:
            return {0: 1.0}
            
        phi = phase_u / self.config.phase_reset_value # Normalizar al manifold
        
        # Fase escalada que "ve" esta ventana
        theta = (phi * (2 ** offset)) % 1.0
        
        probabilities = {}
        for y in range(N):
            # Caso ideal: y = round(theta * N)
            if np.isclose(theta * N, y, atol=1e-9):
                prob = 1.0
            else:
                # Amplitud de probabilidad estándar de QPE (Fórmula de Dirichlet Kernel)
                delta = theta * N - y
                # prob = |(1/N) * sin(πΔ) / sin(πΔ/N)|^2
                prob = (np.sin(np.pi * delta) / (N * np.sin(np.pi * delta / N)))**2
            
            probabilities[y] = prob
            
        # Validar y normalizar (por errores numéricos)
        total_p = sum(probabilities.values())
        for y in probabilities:
            probabilities[y] /= total_p
            
        return probabilities

    def measure_and_collapse(self, probabilities: Dict[int, float]) -> Dict[int, int]:
        """
        Simulación estocástica de N shots.
        """
        n_shots = self.config.n_shots
        outcomes = list(probabilities.keys())
        probs = list(probabilities.values())
        
        measurements = np.random.choice(outcomes, size=n_shots, p=probs)
        
        histogram = {}
        for m in measurements:
            histogram[int(m)] = histogram.get(int(m), 0) + 1
            
        return histogram
    
    def execute_block(self, block_index: int) -> BlockResult:
        """
        Ejecutar secuencia completa para un bloque.
        
        Coordina: Inicialización → Phase Kickback → IQFT → Medición
        
        Args:
            block_index: Índice del bloque (0 es LSB)
        
        Returns:
            BlockResult con estadísticas completas
        """
        # II.1 Inicialización (Superposición de control)
        _ = self.initialize_qubits()
        
        # II.2 Phase Kickback (Teórico)
        phase_u, m_bits, offset = self.phase_kickback(block_index)
        
        # II.3 Simulación de IQFT
        probabilities = self.simulate_qpe_distribution(phase_u, m_bits, offset)
        
        # II.4 Medición y Colapso
        final_histogram = self.measure_and_collapse(probabilities)
        final_probs = {k: v / self.config.n_shots for k, v in final_histogram.items()}
        
        # Construir BlockResult
        top_candidates = sorted(final_probs.items(), key=lambda x: x[1], reverse=True)[:2]
        
        phase_bits = format(top_candidates[0][0], f'0{m_bits}b')
        
        ambiguity_ratio = (
            top_candidates[1][1] / top_candidates[0][1]
            if len(top_candidates) > 1 else 0.0
        )
        
        confidence = top_candidates[0][1]
        
        block_result = BlockResult(
            block_index=block_index,
            window_size=self.config.window_size,
            measurement_histogram=final_histogram,
            top_candidates=top_candidates,
            phase_bits=phase_bits,
            ambiguity_ratio=ambiguity_ratio,
            confidence=confidence
        )
        
        self.results.append(block_result)
        return block_result


# ============================================================================
# MÓDULO III: RESOLUCIÓN DE AMBIGÜEDAD
# ============================================================================

class AmbiguityResolution:
    """Encapsula la Fase de Resolución de Ambigüedad (Post-procesamiento)."""
    
    def __init__(self, config: AWQPEConfig):
        """
        Args:
            config: Configuración del protocolo
        """
        self.config = config
    
    def identify_candidates(self, histogram: Dict[int, float]) -> List[Tuple[int, float]]:
        """
        III.1 Identificación de Candidatos: Seleccionar dos más probables.
        
        Args:
            histogram: Diccionario de valores y probabilidades
        
        Returns:
            Lista de (valor, probabilidad) ordenada por probabilidad
        """
        sorted_candidates = sorted(histogram.items(), key=lambda x: x[1], reverse=True)
        return sorted_candidates[:2]
    
    def compute_ambiguity_ratio(self, candidates: List[Tuple[int, float]]) -> float:
        """
        III.2 Cálculo de Ratio de Ambigüedad: p2/p1 vs ϵ.
        
        Args:
            candidates: Lista de candidatos con probabilidades
        
        Returns:
            Ratio p2/p1
        """
        if len(candidates) < 2:
            return 0.0
        
        p1 = candidates[0][1]
        p2 = candidates[1][1]
        
        return p2 / p1 if p1 > 0 else 0.0
    
    def apply_lsb_to_msb_correction(
        self,
        current_block_bits: str,
        prev_block_bits: Optional[str],
        ambiguity_ratio: float
    ) -> Tuple[str, Optional[int]]:
        """
        III.3 Corrección LSB-to-MSB: Usar bit MSB para corregir bloque anterior.
        
        Args:
            current_block_bits: Bits del bloque actual
            prev_block_bits: Bits del bloque anterior (None si es el primero)
            ambiguity_ratio: Ratio de ambigüedad actual
        
        Returns:
            Tupla (bits corregidos, bit de corrección si aplica)
        """
        # Detectar "Special Chunk": fase exactamente 0.5
        is_special_chunk = (
            current_block_bits == '1' * len(current_block_bits) or
            current_block_bits == '0' * len(current_block_bits)
        )
        
        correction_bit = None
        corrected_bits = current_block_bits
        
        # Si hay ambigüedad alta y bloque anterior, aplicar corrección
        if (prev_block_bits is not None and 
            ambiguity_ratio > self.config.ambiguity_threshold):
            
            # Tomar prestado del MSB del bloque anterior
            msb_prev = int(prev_block_bits[-1])
            
            # Ajuste adaptativo para Special Chunk
            if is_special_chunk:
                correction_bit = 1 - msb_prev
                corrected_bits = bin(int(current_block_bits, 2) + correction_bit)[2:].zfill(len(current_block_bits))
        
        return corrected_bits, correction_bit
    
    def resolve_ambiguities(
        self,
        block_results: List[BlockResult]
    ) -> List[str]:
        """
        Resolver ambigüedades para todos los bloques (LSB a MSB).
        
        Args:
            block_results: Lista de resultados de bloques
        
        Returns:
            Lista de bits de fase corregidos
        """
        corrected_bits_list = []
        prev_bits = None
        
        for block_result in block_results:
            current_bits = block_result.phase_bits
            
            # Aplicar corrección
            corrected_bits, correction = self.apply_lsb_to_msb_correction(
                current_bits,
                prev_bits,
                block_result.ambiguity_ratio
            )
            
            block_result.phase_bits = corrected_bits
            block_result.required_correction = correction
            
            corrected_bits_list.append(corrected_bits)
            prev_bits = corrected_bits
        
        return corrected_bits_list


# ============================================================================
# MÓDULO IV: RECONSTRUCCIÓN FINAL
# ============================================================================

class FinalReconstruction:
    """Encapsula la Fase de Reconstrucción Final."""
    
    def __init__(self, config: AWQPEConfig):
        """
        Args:
            config: Configuración del protocolo
        """
        self.config = config
    
    def concatenate_bits(self, bits_list: List[str]) -> str:
        """
        IV.1 Concatenación: Bloque 0 es MSB (Powers 2^0, 2^1, ...).
        Siguiendo el slide 9, las ventanas se concatenan con solapamiento.
        """
        if not bits_list:
            return ""
            
        # El primer bloque (W0) es el más significativo (MSBs).
        # Los bloques se solapan en 1 bit: LSB(W_i) == MSB(W_i+1).
        # Para reconstruir, usamos el MSB de la ventana siguiente (que es más estable).
        
        full_bits = ""
        for i in range(len(bits_list) - 1):
            # Tomar todos los bits excepto el último (LSB de la ventana)
            full_bits += bits_list[i][:-1]
            
        # Añadir el último bloque completo
        full_bits += bits_list[-1]
        
        # Recortar si excede la precisión total (debido al solapamiento)
        return full_bits[:self.config.total_precision_bits]
    
    def bits_to_phase(self, phase_bits: str) -> float:
        """
        Convertir cadena de bits a valor de fase.
        
        ϕ = (valor binario) / 2^n
        
        Args:
            phase_bits: Cadena de bits (p.ej., "01010101")
        
        Returns:
            Fase en radianes (normalizada a [-π, π])
        """
        # Convertir de binario a decimal
        decimal_value = int(phase_bits, 2)
        
        # Normalizar a [0, 1)
        n_bits = len(phase_bits)
        normalized_phase = decimal_value / (2 ** n_bits)
        
        # Convertir a radianes [0, 2π)
        # Convertir a radianes [0, P) - Reajuste Metripléptico
        phase_radians = normalized_phase * self.config.phase_reset_value
        
        # Normalizar: si excede el umbral, reiniciar (Metriplectic Reset)
        phase_normalized = phase_radians % self.config.phase_reset_value
        
        return phase_normalized
    
    def validate_physics(
        self,
        phase_estimate: float,
        block_results: List[BlockResult]
    ) -> Tuple[bool, float]:
        """
        IV.2 Validación Física: Verificar límites de coherencia.
        
        Args:
            phase_estimate: Estimación de fase en radianes
            block_results: Resultados de bloques para análisis
        
        Returns:
            Tupla (es_válido, error_total)
        """
        valid = True
        total_error = 0.0
        
        # Verificar rango de fase
        min_phase, max_phase = self.config.max_phase_range
        if not (min_phase <= phase_estimate <= max_phase):
            valid = False
        
        # Calcular error acumulado por bloque
        for i, block_result in enumerate(block_results):
            # Error por incertidumbre en medición
            error_block = 1.0 / (2 ** (block_result.window_size * (i + 1)))
            total_error += error_block
            
            # Penalizar si hay ambigüedad alta
            if block_result.ambiguity_ratio > self.config.ambiguity_threshold:
                total_error *= 1.5  # Penalización de 50%
        
        # Verificar coherencia
        if self.config.validate_physics:
            # Error máximo basado en tiempo de coherencia
            expected_precision = 1.0 / (2 ** self.config.total_precision_bits)
            coherence_error = self.config.coherence_time / expected_precision
            
            if total_error > coherence_error:
                warnings.warn(
                import warnings
                    f"Error estimado ({total_error:.2e}) exceede coherencia ({coherence_error:.2e})"
                )
        
        return valid, total_error
    
    def reconstruct(
        self,
        block_results: List[BlockResult]
    ) -> PhaseEstimationResult:
        """
        Ejecutar reconstrucción completa.
        
        Args:
            block_results: Resultados de todos los bloques
        
        Returns:
            PhaseEstimationResult con estimación final
        """
        # IV.1 Concatenación
        bits_list = [br.phase_bits for br in block_results]
        phase_bits = self.concatenate_bits(bits_list)
        
        # Convertir a fase
        phase_estimate = self.bits_to_phase(phase_bits)
        
        # IV.2 Validación
        valid, total_error = self.validate_physics(phase_estimate, block_results)
        
        # Crear resultado final
        result = PhaseEstimationResult(
            phase_estimate=phase_estimate,
            phase_bits=phase_bits,
            block_results=block_results,
            total_error=total_error,
            coherence_validated=valid
        )
        
        return result


# ============================================================================
# CLASE PRINCIPAL: EJECUTOR DEL PROTOCOLO AWQPE
# ============================================================================

class AWQPEProtocol:
    """
    Ejecutor principal del protocolo AWQPE.
    
    Coordina todas las fases: Setup → Ejecución → Resolución → Reconstrucción
    """
    
    def __init__(self, config: AWQPEConfig, operator: QuantumOperator):
        """
        Args:
            config: Configuración del protocolo
            operator: Operador unitario U con autoestado |u⟩
        """
        self.config = config
        self.operator = operator
        
        # Inicializar módulos
        self.setup = SetupPhase(config, operator)
        self.execution = QuantumCircuitExecution(config, operator)
        self.ambiguity = AmbiguityResolution(config)
        self.reconstruction = FinalReconstruction(config)
    
    def run(self, verbose: bool = True) -> PhaseEstimationResult:
        """
        Ejecutar protocolo AWQPE completo.
        
        Args:
            verbose: Mostrar información detallada
        
        Returns:
            PhaseEstimationResult con la estimación final
        
        Raises:
            PhaseEstimationError: Si hay errores durante la ejecución
        """
        if verbose:
            print(self.setup.generate_report())
        
        # Fase II: Ejecución
        if verbose:
            print("\n" + "=" * 70)
            print("FASE DE EJECUCIÓN (PROCESSING)")
            print("=" * 70 + "\n")
        
        for window_index in range(self.config.num_windows):
            block_result = self.execution.execute_block(window_index)
            
            if verbose:
                print(f"Bloque {window_index}:")
                print(f"  Bits de fase: {block_result.phase_bits}")
                print(f"  Confianza: {block_result.confidence:.4f}")
                print(f"  Ratio de ambigüedad: {block_result.ambiguity_ratio:.4f}")
                if block_result.required_correction is not None:
                    print(f"  Corrección aplicada: {block_result.required_correction}")
                print()
        
        # Fase III: Resolución de ambigüedad
        if verbose:
            print("=" * 70)
            print("FASE DE RESOLUCIÓN DE AMBIGÜEDAD (POST-PROCESSING)")
            print("=" * 70 + "\n")
        
        corrected_bits = self.ambiguity.resolve_ambiguities(self.execution.results)
        
        if verbose:
            print("Bits corregidos por bloque:")
            for i, bits in enumerate(corrected_bits):
                print(f"  Bloque {i}: {bits}")
            print()
        
        # Fase IV: Reconstrucción
        if verbose:
            print("=" * 70)
            print("FASE DE RECONSTRUCCIÓN FINAL (RECONSTRUCTION)")
            print("=" * 70 + "\n")
        
        result = self.reconstruction.reconstruct(self.execution.results)
        
        if verbose:
            print(result)
        
        return result
    
    def generate_full_report(self, result: PhaseEstimationResult) -> str:
        """Generar reporte completo de ejecución."""
        report = self.setup.generate_report()
        
        report += "\n" + "=" * 70 + "\n"
        report += "FASE DE EJECUCIÓN - RESULTADOS POR BLOQUE\n"
        report += "=" * 70 + "\n\n"
        
        for br in result.block_results:
            report += f"Bloque {br.block_index}:\n"
            report += f"  Bits: {br.phase_bits}\n"
            report += f"  Confianza: {br.confidence:.4f}\n"
            report += f"  Ratio de ambigüedad: {br.ambiguity_ratio:.4f}\n"
            report += f"  Top candidatos: {br.top_candidates}\n"
            if br.required_correction is not None:
                report += f"  Corrección: {br.required_correction}\n"
            report += "\n"
        
        report += "=" * 70 + "\n"
        report += "RESULTADO FINAL\n"
        report += "=" * 70 + "\n"
        report += str(result)
        
        return report
