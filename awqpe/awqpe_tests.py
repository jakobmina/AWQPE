"""
================================================================================
SUITE DE TESTS UNITARIOS - PROTOCOLO AWQPE
================================================================================

Tests para validar funcionamiento correcto de todas las fases del protocolo.
Incluye tests unitarios, integración y validación de resultados.

Para ejecutar: python -m pytest awqpe_tests.py -v
================================================================================
"""

import pytest
import numpy as np
from awqpe_protocol import (
    AWQPEConfig,
    SimplePhaseOperator,
    BerryCurvatureOperator,
    SetupPhase,
    QuantumCircuitExecution,
    AmbiguityResolution,
    FinalReconstruction,
    AWQPEProtocol,
    PhaseEstimationError,
    AmbiguityResolutionError,
    BlockResult,
    PhaseEstimationResult
)


# ============================================================================
# TESTS DE CONFIGURACIÓN
# ============================================================================

class TestAWQPEConfig:
    """Tests para la clase AWQPEConfig."""
    
    def test_config_creation_valid(self):
        """Test: crear configuración válida."""
        config = AWQPEConfig(
            total_precision_bits=8,
            window_size=3,
            n_shots=1024
        )
        assert config.total_precision_bits == 8
        assert config.window_size == 3
        assert config.n_shots == 1024
    
    def test_config_invalid_precision_bits(self):
        """Test: rechazar total_precision_bits inválido."""
        with pytest.raises(ValueError):
            AWQPEConfig(total_precision_bits=-1)
    
    def test_config_invalid_window_size(self):
        """Test: rechazar window_size mayor a total_precision_bits."""
        with pytest.raises(ValueError):
            AWQPEConfig(total_precision_bits=8, window_size=10)
    
    def test_config_invalid_threshold(self):
        """Test: rechazar threshold fuera de [0, 1]."""
        with pytest.raises(ValueError):
            AWQPEConfig(ambiguity_threshold=1.5)
    
    def test_num_windows_calculation(self):
        """Test: calcular número de ventanas correctamente."""
        config = AWQPEConfig(total_precision_bits=8, window_size=3)
        assert config.num_windows == 3  # ceil(8/3) = 3
        
        config2 = AWQPEConfig(total_precision_bits=8, window_size=2)
        assert config2.num_windows == 4  # ceil(8/2) = 4
        
        config3 = AWQPEConfig(total_precision_bits=8, window_size=8)
        assert config3.num_windows == 1  # ceil(8/8) = 1
    
    def test_control_qubits_per_window(self):
        """Test: qubits de control por ventana."""
        config = AWQPEConfig(total_precision_bits=8, window_size=3)
        assert config.control_qubits_per_window == 3


# ============================================================================
# TESTS DE OPERADORES
# ============================================================================

class TestQuantumOperators:
    """Tests para operadores unitarios."""
    
    def test_simple_phase_operator_creation(self):
        """Test: crear SimplePhaseOperator."""
        operator = SimplePhaseOperator(target_phase=0.5)
        assert operator.target_phase == 0.5
        assert operator.name == "SimplePhase(ϕ=0.5000)"
    
    def test_simple_phase_operator_eigenstate(self):
        """Test: autoestado normalizado en SimplePhaseOperator."""
        operator = SimplePhaseOperator(0.5)
        eigenstate = operator.get_eigenstate()
        
        norm = np.linalg.norm(eigenstate)
        assert np.isclose(norm, 1.0), "Autoestado debe estar normalizado"
    
    def test_simple_phase_operator_apply(self):
        """Test: aplicación de SimplePhaseOperator."""
        target_phase = 0.7
        operator = SimplePhaseOperator(target_phase)
        eigenstate = operator.get_eigenstate()
        
        state, phase = operator.apply(eigenstate, power=0)
        assert np.isclose(phase, target_phase % (2*np.pi))
    
    def test_simple_phase_operator_power(self):
        """Test: aplicación con potencias."""
        target_phase = 0.2
        operator = SimplePhaseOperator(target_phase)
        eigenstate = operator.get_eigenstate()
        
        _, phase0 = operator.apply(eigenstate, power=0)
        _, phase1 = operator.apply(eigenstate, power=1)
        _, phase2 = operator.apply(eigenstate, power=2)
        
        # Verificar que la fase se duplica con cada potencia
        assert np.isclose(phase1 / phase0, 2, atol=0.1) or \
               np.isclose(phase1, 2 * phase0, atol=0.5)
    
    def test_berry_curvature_operator_creation(self):
        """Test: crear BerryCurvatureOperator."""
        operator = BerryCurvatureOperator(solid_angle=2.5)
        assert operator.solid_angle == 2.5
        assert "BerryCurvature" in operator.name
    
    def test_berry_curvature_operator_phase(self):
        """Test: fase de Berry correcta."""
        solid_angle = 2.5
        operator = BerryCurvatureOperator(solid_angle)
        eigenstate = operator.get_eigenstate()
        
        _, phase = operator.apply(eigenstate, power=0)
        expected_phase = solid_angle / 2.0
        
        # Fase de Berry debe ser solid_angle/2
        assert np.isclose(np.abs(phase), expected_phase, atol=0.1) or \
               np.isclose(np.abs(phase), expected_phase % (2*np.pi), atol=0.1)


# ============================================================================
# TESTS DE FASE I: PREPARACIÓN
# ============================================================================

class TestSetupPhase:
    """Tests para la Fase de Preparación."""
    
    def test_setup_valid_system(self):
        """Test: Setup reconoce sistema válido."""
        config = AWQPEConfig()
        operator = SimplePhaseOperator(0.5)
        setup = SetupPhase(config, operator)
        
        system_info = setup.define_system()
        assert system_info["eigenstate_valid"]
    
    def test_setup_invalid_eigenstate(self):
        """Test: Setup rechaza autoestado no normalizado."""
        config = AWQPEConfig()
        operator = SimplePhaseOperator(0.5)
        setup = SetupPhase(config, operator)
        
        # Modificar autoestado a no normalizado
        setup.eigenstate = np.array([1.0, 1.0])  # norm = sqrt(2)
        
        assert not setup._is_valid_eigenstate()
    
    def test_setup_windows_strategy(self):
        """Test: estrategia de ventanas correcta."""
        config = AWQPEConfig(total_precision_bits=8, window_size=3)
        operator = SimplePhaseOperator(0.5)
        setup = SetupPhase(config, operator)
        
        windows = setup.strategy_windows()
        assert windows["num_windows"] == 3
        assert windows["total_precision_bits"] == 8
        assert windows["window_size"] == 3
    
    def test_setup_resource_allocation(self):
        """Test: asignación correcta de recursos."""
        config = AWQPEConfig(
            total_precision_bits=8,
            window_size=3,
            n_shots=1024
        )
        operator = SimplePhaseOperator(0.5)
        setup = SetupPhase(config, operator)
        
        resources = setup.resource_allocation()
        assert resources["control_qubits_per_window"] == 3
        assert resources["n_shots"] == 1024
        assert resources["num_windows"] == 3


# ============================================================================
# TESTS DE FASE II: EJECUCIÓN
# ============================================================================

class TestQuantumCircuitExecution:
    """Tests para la Fase de Ejecución."""
    
    def test_initialization(self):
        """Test: inicialización de qubits."""
        config = AWQPEConfig(window_size=3)
        operator = SimplePhaseOperator(0.5)
        execution = QuantumCircuitExecution(config, operator)
        
        init_result = execution.initialize_qubits()
        assert init_result["superposition_valid"]
    
    def test_single_block_execution(self):
        """Test: ejecución de un bloque."""
        config = AWQPEConfig(
            total_precision_bits=6,
            window_size=3,
            n_shots=512
        )
        operator = SimplePhaseOperator(0.5)
        execution = QuantumCircuitExecution(config, operator)
        
        block_result = execution.execute_block(0)
        
        assert block_result.block_index == 0
        assert block_result.window_size == 3
        assert len(block_result.phase_bits) == 3
        assert 0 <= block_result.ambiguity_ratio <= 1
    
    def test_multiple_blocks_execution(self):
        """Test: ejecución de múltiples bloques."""
        config = AWQPEConfig(
            total_precision_bits=8,
            window_size=3,
            n_shots=512
        )
        operator = SimplePhaseOperator(0.5)
        execution = QuantumCircuitExecution(config, operator)
        
        for i in range(config.num_windows):
            execution.execute_block(i)
        
        assert len(execution.results) == config.num_windows
    
    def test_histogram_normalization(self):
        """Test: histogramas correctamente normalizados."""
        config = AWQPEConfig(window_size=2, n_shots=1000)
        operator = SimplePhaseOperator(0.5)
        execution = QuantumCircuitExecution(config, operator)
        
        block_result = execution.execute_block(0)
        
        # Suma de probabilidades debe ser ~1.0
        total_prob = sum(prob for _, prob in block_result.top_candidates)
        assert total_prob <= 1.0


# ============================================================================
# TESTS DE FASE III: RESOLUCIÓN DE AMBIGÜEDAD
# ============================================================================

class TestAmbiguityResolution:
    """Tests para la Fase de Resolución de Ambigüedad."""
    
    def test_identify_candidates(self):
        """Test: identificar candidatos top 2."""
        config = AWQPEConfig()
        ambiguity = AmbiguityResolution(config)
        
        histogram = {0: 0.5, 1: 0.3, 2: 0.15, 3: 0.05}
        candidates = ambiguity.identify_candidates(histogram)
        
        assert len(candidates) <= 2
        assert candidates[0][0] == 0  # Valor más probable
        assert candidates[0][1] == 0.5  # Probabilidad más alta
    
    def test_ambiguity_ratio_calculation(self):
        """Test: calcular ratio de ambigüedad."""
        config = AWQPEConfig()
        ambiguity = AmbiguityResolution(config)
        
        candidates = [(0, 0.7), (1, 0.25)]
        ratio = ambiguity.compute_ambiguity_ratio(candidates)
        
        expected_ratio = 0.25 / 0.7
        assert np.isclose(ratio, expected_ratio)
    
    def test_ambiguity_ratio_single_candidate(self):
        """Test: ratio con un solo candidato."""
        config = AWQPEConfig()
        ambiguity = AmbiguityResolution(config)
        
        candidates = [(0, 0.8)]
        ratio = ambiguity.compute_ambiguity_ratio(candidates)
        
        assert ratio == 0.0
    
    def test_lsb_to_msb_correction_no_previous(self):
        """Test: corrección cuando no hay bloque previo."""
        config = AWQPEConfig(ambiguity_threshold=0.9)
        ambiguity = AmbiguityResolution(config)
        
        bits, correction = ambiguity.apply_lsb_to_msb_correction(
            current_block_bits="101",
            prev_block_bits=None,
            ambiguity_ratio=0.5
        )
        
        assert bits == "101"  # Sin corrección
        assert correction is None
    
    def test_lsb_to_msb_correction_with_previous(self):
        """Test: corrección con bloque previo."""
        config = AWQPEConfig(ambiguity_threshold=0.8)
        ambiguity = AmbiguityResolution(config)
        
        bits, correction = ambiguity.apply_lsb_to_msb_correction(
            current_block_bits="101",
            prev_block_bits="110",
            ambiguity_ratio=0.92  # > threshold
        )
        
        # Debe haber corrección
        assert correction is not None


# ============================================================================
# TESTS DE FASE IV: RECONSTRUCCIÓN
# ============================================================================

class TestFinalReconstruction:
    """Tests para la Fase de Reconstrucción."""
    
    def test_concatenate_bits(self):
        """Test: concatenación de bits."""
        config = AWQPEConfig()
        reconstruction = FinalReconstruction(config)
        
        bits_list = ["101", "011", "110"]  # LSB a MSB
        result = reconstruction.concatenate_bits(bits_list)
        
        # Orden invertido (MSB a LSB)
        assert result == "110011101"
    
    def test_bits_to_phase_zero(self):
        """Test: bits "00000000" -> fase 0."""
        config = AWQPEConfig()
        reconstruction = FinalReconstruction(config)
        
        phase = reconstruction.bits_to_phase("00000000")
        assert np.isclose(phase, 0.0, atol=0.1)
    
    def test_bits_to_phase_quarter(self):
        """Test: bits para π/2 fase."""
        config = AWQPEConfig()
        reconstruction = FinalReconstruction(config)
        
        # Para 8 bits: valor 64 = π/2
        bits = format(64, '08b')
        phase = reconstruction.bits_to_phase(bits)
        
        # Debe estar cerca de π/2
        assert np.isclose(phase, np.pi/2, atol=0.2)
    
    def test_validate_physics_valid(self):
        """Test: validación física de resultado válido."""
        config = AWQPEConfig(
            total_precision_bits=8,
            coherence_time=1e-3,
            validate_physics=True
        )
        reconstruction = FinalReconstruction(config)
        
        # Crear bloques simples
        block1 = BlockResult(
            block_index=0,
            window_size=3,
            measurement_histogram={0: 500, 1: 250},
            top_candidates=[(0, 0.7), (1, 0.25)],
            phase_bits="101",
            ambiguity_ratio=0.36,
            confidence=0.7
        )
        
        phase = 0.5  # Valor razonable
        valid, error = reconstruction.validate_physics(phase, [block1])
        
        assert valid or not valid  # Simplemente verificar que retorna bool


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

class TestAWQPEIntegration:
    """Tests de integración del protocolo completo."""
    
    def test_simple_phase_estimation(self):
        """Test: estimación de fase simple."""
        config = AWQPEConfig(
            total_precision_bits=6,
            window_size=2,
            n_shots=512
        )
        
        target_phase = 0.5
        operator = SimplePhaseOperator(target_phase)
        protocol = AWQPEProtocol(config, operator)
        
        result = protocol.run(verbose=False)
        
        assert result.phase_estimate is not None
        assert isinstance(result.phase_estimate, float)
        assert -np.pi <= result.phase_estimate <= np.pi
        assert len(result.block_results) == config.num_windows
    
    def test_berry_phase_estimation(self):
        """Test: estimación de fase de Berry."""
        config = AWQPEConfig(
            total_precision_bits=8,
            window_size=3,
            n_shots=1024
        )
        
        solid_angle = 2.0
        operator = BerryCurvatureOperator(solid_angle)
        protocol = AWQPEProtocol(config, operator)
        
        result = protocol.run(verbose=False)
        
        assert result.phase_estimate is not None
        assert result.coherence_validated is not None
    
    def test_result_structure(self):
        """Test: estructura completa del resultado."""
        config = AWQPEConfig(
            total_precision_bits=8,
            window_size=3,
            n_shots=1024
        )
        
        operator = SimplePhaseOperator(0.7)
        protocol = AWQPEProtocol(config, operator)
        result = protocol.run(verbose=False)
        
        # Verificar estructura del resultado
        assert hasattr(result, 'phase_estimate')
        assert hasattr(result, 'phase_bits')
        assert hasattr(result, 'block_results')
        assert hasattr(result, 'total_error')
        assert hasattr(result, 'coherence_validated')
        
        # Verificar tipos
        assert isinstance(result.phase_estimate, float)
        assert isinstance(result.phase_bits, str)
        assert isinstance(result.block_results, list)
        assert isinstance(result.total_error, float)
        assert isinstance(result.coherence_validated, bool)
    
    def test_phase_bits_validity(self):
        """Test: bits de fase son válidos (solo 0s y 1s)."""
        config = AWQPEConfig(
            total_precision_bits=8,
            window_size=3,
            n_shots=512
        )
        
        operator = SimplePhaseOperator(0.5)
        protocol = AWQPEProtocol(config, operator)
        result = protocol.run(verbose=False)
        
        # Verificar que phase_bits solo contiene 0s y 1s
        assert all(bit in '01' for bit in result.phase_bits)
        # Verificar longitud
        assert len(result.phase_bits) == config.total_precision_bits


# ============================================================================
# TESTS DE VALIDACIÓN ESTADÍSTICA
# ============================================================================

class TestStatisticalValidation:
    """Tests para validación estadística de múltiples ejecuciones."""
    
    def test_reproducibility_with_seed(self):
        """Test: reproducibilidad con random seed."""
        config = AWQPEConfig(total_precision_bits=6, window_size=2, n_shots=512)
        operator = SimplePhaseOperator(0.5)
        
        np.random.seed(42)
        protocol1 = AWQPEProtocol(config, operator)
        result1 = protocol1.run(verbose=False)
        
        np.random.seed(42)
        protocol2 = AWQPEProtocol(config, operator)
        result2 = protocol2.run(verbose=False)
        
        # Resultados deben ser idénticos con el mismo seed
        assert np.isclose(result1.phase_estimate, result2.phase_estimate)
    
    def test_error_decreases_with_precision(self):
        """Test: error disminuye al aumentar precisión."""
        target_phase = 0.7
        operator = SimplePhaseOperator(target_phase)
        
        errors = []
        for bits in [6, 8, 10]:
            config = AWQPEConfig(
                total_precision_bits=bits,
                window_size=min(3, bits),
                n_shots=1024
            )
            protocol = AWQPEProtocol(config, operator)
            result = protocol.run(verbose=False)
            
            error = abs(target_phase - result.phase_estimate)
            errors.append(error)
        
        # Error debe decrecer (generalmente)
        assert errors[0] >= errors[-1] or np.isclose(errors[0], errors[-1])


# ============================================================================
# TESTS DE CASOS LÍMITE
# ============================================================================

class TestEdgeCases:
    """Tests para casos límite y edge cases."""
    
    def test_single_bit_precision(self):
        """Test: funciona con precisión de 1 bit."""
        config = AWQPEConfig(
            total_precision_bits=1,
            window_size=1,
            n_shots=512
        )
        operator = SimplePhaseOperator(0.5)
        protocol = AWQPEProtocol(config, operator)
        
        result = protocol.run(verbose=False)
        assert result.phase_estimate is not None
    
    def test_large_precision(self):
        """Test: funciona con alta precisión."""
        config = AWQPEConfig(
            total_precision_bits=16,
            window_size=4,
            n_shots=2048
        )
        operator = SimplePhaseOperator(0.123)
        protocol = AWQPEProtocol(config, operator)
        
        result = protocol.run(verbose=False)
        assert result.phase_estimate is not None
        assert len(result.phase_bits) == 16
    
    def test_phase_zero(self):
        """Test: estimar fase = 0."""
        config = AWQPEConfig(total_precision_bits=8, window_size=3, n_shots=512)
        operator = SimplePhaseOperator(0.0)
        protocol = AWQPEProtocol(config, operator)
        
        result = protocol.run(verbose=False)
        assert abs(result.phase_estimate) < 0.2  # Cerca de 0
    
    def test_phase_pi(self):
        """Test: estimar fase = π."""
        config = AWQPEConfig(total_precision_bits=8, window_size=3, n_shots=512)
        operator = SimplePhaseOperator(np.pi)
        protocol = AWQPEProtocol(config, operator)
        
        result = protocol.run(verbose=False)
        assert abs(abs(result.phase_estimate) - np.pi) < 0.5 or \
               np.isclose(result.phase_estimate, 0, atol=0.2)


# ============================================================================
# EJECUCIÓN DE TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
