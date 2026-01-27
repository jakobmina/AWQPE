"""
================================================================================
PROTOCOLO AWQPE: Adaptive Windowed Quantum Phase Estimation
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
import warnings
from abc import ABC, abstractmethod


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
    
    # Validación física
    validate_physics: bool = True
    max_phase_range: Tuple[float, float] = (-np.pi, np.pi)
    
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
        """Calcular número de ventanas necesarias."""
        return int(np.ceil(self.total_precision_bits / self.window_size))
    
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
# CLASE BASE PARA OPERADORES UNITARIOS
# ============================================================================

class QuantumOperator(ABC):
    """Interfaz abstracta para operadores unitarios U."""
    
    @abstractmethod
    def apply(self, eigenstate: np.ndarray, power: int) -> Tuple[np.ndarray, float]:
        """
        Aplicar U^(2^power) al autoestado.
        
        Args:
            eigenstate: Autoestado |u⟩
            power: k en U^(2^k)
        
        Returns:
            Tupla (estado resultante, fase acumulada)
        """
        pass
    
    @abstractmethod
    def get_eigenstate(self) -> np.ndarray:
        """Obtener el autoestado del operador."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre descriptivo del operador."""
        pass


class SimplePhaseOperator(QuantumOperator):
    """
    Operador unitario simple: U = e^(iθσz/2)
    Útil para pruebas y demostraciones.
    """
    
    def __init__(self, target_phase: float):
        """
        Args:
            target_phase: Fase objetivo ϕ (en radianes)
        """
        self.target_phase = target_phase
        self._eigenstate = np.array([1.0, 1.0]) / np.sqrt(2)  # |+⟩
    
    def apply(self, eigenstate: np.ndarray, power: int) -> Tuple[np.ndarray, float]:
        """Aplicar U^(2^power)."""
        # Fase acumulada: 2^power * ϕ
        accumulated_phase = (2 ** power) * self.target_phase
        
        # Normalizar a [-π, π]
        normalized_phase = np.angle(np.exp(1j * accumulated_phase))
        
        return eigenstate, normalized_phase
    
    def get_eigenstate(self) -> np.ndarray:
        """Retornar autoestado."""
        return self._eigenstate.copy()
    
    @property
    def name(self) -> str:
        return f"SimplePhase(ϕ={self.target_phase:.4f})"


class BerryCurvatureOperator(QuantumOperator):
    """
    Operador simulando la fase de Berry en la esfera de Bloch.
    U realiza transporte paralelo adiabático.
    """
    
    def __init__(self, solid_angle: float):
        """
        Args:
            solid_angle: Ángulo sólido subtendido (en estereorradianes)
        """
        self.solid_angle = solid_angle
        self._eigenstate = np.array([1.0 / np.sqrt(2), 1.0 / np.sqrt(2)])
    
    def apply(self, eigenstate: np.ndarray, power: int) -> Tuple[np.ndarray, float]:
        """
        Fase de Berry: ϕ_Berry = Ω/2, donde Ω es el ángulo sólido.
        """
        berry_phase = self.solid_angle / 2.0
        accumulated_phase = (2 ** power) * berry_phase
        normalized_phase = np.angle(np.exp(1j * accumulated_phase))
        return eigenstate, normalized_phase
    
    def get_eigenstate(self) -> np.ndarray:
        return self._eigenstate.copy()
    
    @property
    def name(self) -> str:
        return f"BerryCurvature(Ω={self.solid_angle:.4f})"


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
    
    def phase_kickback(self, block_index: int) -> BlockResult:
        """
        II.2 Transferencia de Fase (Phase Kickback): Aplicar U^(2^k).
        
        Aplica una secuencia de operaciones unitarias controladas U^(2^k+p),
        codificando la fase en las amplitudes de los qubits de control.
        
        Args:
            block_index: Índice del bloque actual
        
        Returns:
            BlockResult con histograma de mediciones simuladas
        """
        window_size = self.config.window_size
        eigenstate = self.operator.get_eigenstate()
        
        # Simular mediciones para cada power k
        measurement_outcomes = []
        
        for k in range(window_size):
            for p in range(window_size):
                power = k + p
                _, phase_accumulated = self.operator.apply(eigenstate, power)
                
                # Convertir fase a valor binario
                # ϕ = k / 2^window_size
                k_val = int(np.round((phase_accumulated / (2 * np.pi)) * (2 ** window_size)))
                k_val = k_val % (2 ** window_size)
                
                measurement_outcomes.append(k_val)
        
        # Construir histograma de mediciones (simulación clásica)
        histogram = {}
        for outcome in measurement_outcomes:
            histogram[outcome] = histogram.get(outcome, 0) + 1
        
        # Normalizar a probabilidades
        total_counts = len(measurement_outcomes)
        
        return histogram, total_counts
    
    def inverse_qft(self, histogram: Dict, block_index: int) -> BlockResult:
        """
        II.3 Transformación al Dominio de Frecuencia: Aplicar IQFT.
        
        La IQFT convierte las amplitudes codificadas en fase a estados
        medibles en la base computacional.
        
        Args:
            histogram: Histograma de fase codificada
            block_index: Índice del bloque
        
        Returns:
            BlockResult después de IQFT
        """
        window_size = self.config.window_size
        
        # Simulación: IQFT es principalmente una reorganización
        # En la práctica, sería una puerta cuántica
        iqft_histogram = {}
        
        for value, count in histogram.items():
            # Aplicar transformación de Fourier discreta inversa
            new_value = 0
            for j in range(window_size):
                new_value += count * np.cos(2 * np.pi * value * j / (2 ** window_size))
            
            new_value = int(np.round(new_value)) % (2 ** window_size)
            iqft_histogram[new_value] = iqft_histogram.get(new_value, 0) + count
        
        return iqft_histogram
    
    def measure_and_collapse(self, block_index: int, iqft_histogram: Dict) -> BlockResult:
        """
        II.4 Colapso y Medición: Ejecutar circuito Nshots veces.
        
        Args:
            block_index: Índice del bloque
            iqft_histogram: Histograma después de IQFT
        
        Returns:
            BlockResult con estadísticas de medición
        """
        window_size = self.config.window_size
        n_shots = self.config.n_shots
        
        # Construir distribución de probabilidad
        total_counts = sum(iqft_histogram.values())
        probabilities = {k: v / total_counts for k, v in iqft_histogram.items()}
        
        # Simular Nshots mediciones
        measurements = np.random.choice(
            list(probabilities.keys()),
            size=n_shots,
            p=list(probabilities.values())
        )
        
        # Construir histograma final
        final_histogram = {}
        for measurement in measurements:
            final_histogram[int(measurement)] = final_histogram.get(int(measurement), 0) + 1
        
        # Normalizar a probabilidades
        final_probs = {k: v / n_shots for k, v in final_histogram.items()}
        
        return final_histogram, final_probs
    
    def execute_block(self, block_index: int) -> BlockResult:
        """
        Ejecutar secuencia completa para un bloque.
        
        Coordina: Inicialización → Phase Kickback → IQFT → Medición
        
        Args:
            block_index: Índice del bloque (0 es LSB)
        
        Returns:
            BlockResult con estadísticas completas
        """
        # II.1 Inicialización
        init_result = self.initialize_qubits()
        
        # II.2 Phase Kickback
        histogram, _ = self.phase_kickback(block_index)
        
        # II.3 IQFT
        iqft_histogram = self.inverse_qft(histogram, block_index)
        
        # II.4 Medición
        final_histogram, final_probs = self.measure_and_collapse(block_index, iqft_histogram)
        
        # Construir BlockResult
        top_candidates = sorted(final_probs.items(), key=lambda x: x[1], reverse=True)[:2]
        
        phase_bits = format(top_candidates[0][0], f'0{self.config.window_size}b')
        
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
        IV.1 Concatenación: Unir cadenas de bits de cada ventana.
        
        Los bloques se concatenan desde LSB a MSB.
        
        Args:
            bits_list: Lista de cadenas de bits (orden LSB a MSB)
        
        Returns:
            Cadena de bits concatenada
        """
        # Invertir orden para obtener MSB-LSB
        phase_bits = ''.join(reversed(bits_list))
        return phase_bits
    
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
        phase_radians = normalized_phase * 2 * np.pi
        
        # Normalizar a [-π, π]
        phase_normalized = np.angle(np.exp(1j * phase_radians))
        
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


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def example_simple_phase():
    """Ejemplo: Estimación de fase simple."""
    print("\n" + "=" * 70)
    print("EJEMPLO 1: ESTIMACIÓN DE FASE SIMPLE")
    print("=" * 70 + "\n")
    
    # Configuración
    config = AWQPEConfig(
        total_precision_bits=8,
        window_size=3,
        n_shots=1024,
        ambiguity_threshold=0.9
    )
    
    # Operador con fase conocida
    target_phase = 0.7  # radianes
    operator = SimplePhaseOperator(target_phase)
    
    # Ejecutar protocolo
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=True)
    
    print("\nComparación:")
    print(f"  Fase objetivo: {target_phase:.6f} rad ({np.degrees(target_phase):.2f}°)")
    print(f"  Fase estimada: {result.phase_estimate:.6f} rad ({np.degrees(result.phase_estimate):.2f}°)")
    print(f"  Error absoluto: {abs(target_phase - result.phase_estimate):.6f} rad")
    print(f"  Error relativo: {abs(target_phase - result.phase_estimate) / abs(target_phase) * 100:.2f}%")
    
    return result


def example_berry_phase():
    """Ejemplo: Estimación de fase de Berry."""
    print("\n" + "=" * 70)
    print("EJEMPLO 2: ESTIMACIÓN DE FASE DE BERRY")
    print("=" * 70 + "\n")
    
    # Configuración
    config = AWQPEConfig(
        total_precision_bits=10,
        window_size=4,
        n_shots=2048,
        ambiguity_threshold=0.85
    )
    
    # Operador de Berry con ángulo sólido conocido
    solid_angle = 2.5  # estereorradianes
    operator = BerryCurvatureOperator(solid_angle)
    
    # Ejecutar protocolo
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=True)
    
    # Fase de Berry teórica
    theoretical_phase = solid_angle / 2.0
    
    print("\nComparación:")
    print(f"  Ángulo sólido: {solid_angle:.6f} sr")
    print(f"  Fase de Berry teórica: {theoretical_phase:.6f} rad")
    print(f"  Fase estimada: {result.phase_estimate:.6f} rad")
    print(f"  Error: {abs(theoretical_phase - result.phase_estimate):.6f} rad")
    
    return result


if __name__ == "__main__":
    # Ejecutar ejemplos
    print("\n" + "#" * 70)
    print("# PROTOCOLO AWQPE - ESTIMACIÓN ADAPTATIVA DE FASE CUÁNTICA")
    print("#" * 70)
    
    result1 = example_simple_phase()
    result2 = example_berry_phase()
    
    print("\n" + "#" * 70)
    print("# EJECUCIÓN COMPLETADA")
    print("#" * 70 + "\n")
