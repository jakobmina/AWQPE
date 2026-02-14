"""
================================================================================
AWQPE QUANTUM OPERATORS
================================================================================

Colección de operadores unitarios U para usar con el protocolo AWQPE.
Cada operador define una fase que el protocolo puede estimar.
================================================================================
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple


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
        self.target_phase = target_phase
        self._eigenstate = np.array([1.0, 1.0]) / np.sqrt(2)  # |+⟩

    def apply(self, eigenstate: np.ndarray, power: int) -> Tuple[np.ndarray, float]:
        accumulated_phase = (2 ** power) * self.target_phase
        normalized_phase = accumulated_phase % 7.0
        return eigenstate, normalized_phase

    def get_eigenstate(self) -> np.ndarray:
        return self._eigenstate.copy()

    @property
    def name(self) -> str:
        return f"SimplePhase(ϕ={self.target_phase:.4f})"


class BerryCurvatureOperator(QuantumOperator):
    """
    Operador simulando la fase de Berry en la esfera de Bloch.
    """

    def __init__(self, solid_angle: float):
        self.solid_angle = solid_angle
        self._eigenstate = np.array([1.0 / np.sqrt(2), 1.0 / np.sqrt(2)])

    def apply(self, eigenstate: np.ndarray, power: int) -> Tuple[np.ndarray, float]:
        berry_phase = self.solid_angle / 2.0
        accumulated_phase = (2 ** power) * berry_phase
        normalized_phase = accumulated_phase % 7.0
        return eigenstate, normalized_phase

    def get_eigenstate(self) -> np.ndarray:
        return self._eigenstate.copy()

    @property
    def name(self) -> str:
        return f"BerryCurvature(Ω={self.solid_angle:.4f})"


class MetriplecticCircuitOperator(QuantumOperator):
    """
    Operador que modela el circuito Metripléptico.
    Estructura: H_0 · CY_12 · Inc_1 · Z^-t_0 · Dec_1
    """

    def __init__(self, time_parameter: float, phase_reset: float = 7.0):
        self.time_parameter = time_parameter
        self.phase_reset = phase_reset
        self._eigenstate = np.ones(8) / np.sqrt(8)

    def apply(self, eigenstate: np.ndarray, power: int) -> Tuple[np.ndarray, float]:
        """
        Aplica el operador U^(2^power).
        """
        phi_golden = (1 + np.sqrt(5)) / 2
        n = self.time_parameter

        o_n = np.cos(np.pi * n) * np.cos(np.pi * phi_golden * n)
        base_phase = (self.time_parameter * self.phase_reset) * o_n
        accumulated_phase = base_phase * (2 ** power)
        normalized_phase = accumulated_phase % self.phase_reset

        return eigenstate, normalized_phase

    def get_eigenstate(self) -> np.ndarray:
        return self._eigenstate.copy()

    @property
    def name(self) -> str:
        return f"MetriplecticCircuit(t={self.time_parameter:.4f})"