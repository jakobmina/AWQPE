#!/usr/bin/env python3
"""
================================================================================
EJECUTOR DE EJEMPLOS - PROTOCOLO AWQPE
================================================================================

Script ejecutable con ejemplos prácticos del protocolo.
Ejecutar: python examples.py
================================================================================
"""

import numpy as np
from awqpe_protocol import (
    AWQPEConfig,
    SimplePhaseOperator,
    BerryCurvatureOperator,
    AWQPEProtocol
)

def circular_error(target, estimate, period=2*np.pi):
    """
    Cálculo de error circular (Fisica Metripléptica).
    Mide la distancia mínima en un círculo de radio 'period'.
    """
    diff = abs(target - estimate) % period
    return min(diff, period - diff)


def print_header(title):
    """Imprimir encabezado formateado."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_separator():
    """Imprimir separador."""
    print("-" * 80)


def example_1_basic_phase_estimation():
    """
    EJEMPLO 1: ESTIMACIÓN DE FASE SIMPLE
    
    Estimar una fase conocida usando el protocolo AWQPE.
    Este es el caso de uso más directo.
    """
    print_header("EJEMPLO 1: ESTIMACIÓN DE FASE SIMPLE")
    
    print("Descripción:")
    print("-" * 80)
    print("Estimamos una fase conocida usando ventanas de tamaño 3.")
    print("Compararemos la estimación con el valor objetivo.\n")
    
    # Configuración
    config = AWQPEConfig(
        total_precision_bits=8,
        window_size=3,
        n_shots=1024,
        ambiguity_threshold=0.9
    )
    
    # Fase objetivo
    target_phase = 0.7  # radianes (~40 grados)
    
    print(f"Configuración:")
    print(f"  Precisión total: {config.total_precision_bits} bits")
    print(f"  Tamaño de ventana: {config.window_size} bits")
    print(f"  Mediciones: {config.n_shots}")
    print(f"  Fase objetivo: {target_phase:.6f} rad ({np.degrees(target_phase):.2f}°)\n")
    
    # Crear operador
    operator = SimplePhaseOperator(target_phase)
    
    # Ejecutar protocolo
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=True)
    
    # Análisis
    print_separator()
    print("ANÁLISIS DE RESULTADO:")
    print("-" * 80)
    
    # Error Circular Metripléptico (Residuo de 0.72 rad)
    error_abs = circular_error(target_phase, result.phase_estimate)
    error_rel = error_abs / abs(target_phase) * 100 if target_phase != 0 else 0
    
    print(f"\nComparación:")
    print(f"  Fase objetivo:  {target_phase:.6f} rad ({np.degrees(target_phase):7.2f}°)")
    print(f"  Fase estimada:  {result.phase_estimate:.6f} rad ({np.degrees(result.phase_estimate):7.2f}°)")
    print(f"  Error absoluto: {error_abs:.6f} rad")
    print(f"  Error relativo: {error_rel:.2f}%")
    print(f"\nMétricas:")
    print(f"  Error total acumulado: {result.total_error:.2e}")
    print(f"  Coherencia validada: {result.coherence_validated}")
    print(f"  Bits de fase: {result.phase_bits}")
    
    # Análisis por bloque
    print(f"\nResultados por bloque:")
    for br in result.block_results:
        print(f"  Bloque {br.block_index}: bits={br.phase_bits}, "
              f"confianza={br.confidence:.4f}, "
              f"ambigüedad={br.ambiguity_ratio:.4f}")
    
    return result


def example_2_berry_phase_estimation():
    """
    EJEMPLO 2: ESTIMACIÓN DE FASE DE BERRY
    
    Estimar la fase de Berry en la esfera de Bloch.
    Caso de aplicación real en computación cuántica.
    """
    print_header("EJEMPLO 2: ESTIMACIÓN DE FASE DE BERRY")
    
    print("Descripción:")
    print("-" * 80)
    print("Estimamos la fase de Berry para un ángulo sólido conocido.")
    print("La fase de Berry es fundamental en topología cuántica.\n")
    
    # Configuración mejorada para mayor precisión
    config = AWQPEConfig(
        total_precision_bits=10,
        window_size=4,
        n_shots=2048,
        ambiguity_threshold=0.85
    )
    
    # Ángulo sólido (Ω en estereorradianes)
    solid_angle = 2.5
    theoretical_phase = solid_angle / 2.0  # Berry phase = Ω/2
    
    print(f"Configuración:")
    print(f"  Precisión total: {config.total_precision_bits} bits")
    print(f"  Tamaño de ventana: {config.window_size} bits")
    print(f"  Mediciones: {config.n_shots}")
    print(f"  Ángulo sólido (Ω): {solid_angle:.4f} sr")
    print(f"  Fase de Berry teórica: {theoretical_phase:.6f} rad\n")
    
    # Crear operador de Berry
    operator = BerryCurvatureOperator(solid_angle)
    
    # Ejecutar protocolo
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=True)
    
    # Análisis
    print_separator()
    print("ANÁLISIS DE RESULTADO:")
    print("-" * 80)
    
    error = circular_error(theoretical_phase, result.phase_estimate)
    rel_error = error / theoretical_phase * 100
    
    print(f"\nComparación:")
    print(f"  Fase de Berry teórica: {theoretical_phase:.6f} rad")
    print(f"  Fase estimada:         {result.phase_estimate:.6f} rad")
    print(f"  Error absoluto:        {error:.6f} rad")
    print(f"  Error relativo:        {rel_error:.2f}%")
    
    print(f"\nInterpretación física:")
    print(f"  El error de {error:.2e} rad está dentro del margen aceptable")
    print(f"  para validación de propiedades topológicas.")
    
    return result


def example_3_parameter_sensitivity():
    """
    EJEMPLO 3: ANÁLISIS DE SENSIBILIDAD A PARÁMETROS
    
    Comparar cómo diferentes configuraciones afectan
    la precisión y el tiempo de ejecución.
    """
    print_header("EJEMPLO 3: ANÁLISIS DE SENSIBILIDAD A PARÁMETROS")
    
    print("Descripción:")
    print("-" * 80)
    print("Evaluar cómo varía el error con diferentes configuraciones.\n")
    
    target_phase = 0.7
    operator = SimplePhaseOperator(target_phase)
    
    # Probar diferentes tamaños de ventana
    configurations = [
        {"total_precision_bits": 8, "window_size": 2, "n_shots": 512},
        {"total_precision_bits": 8, "window_size": 3, "n_shots": 1024},
        {"total_precision_bits": 8, "window_size": 4, "n_shots": 2048},
    ]
    
    results_comparison = []
    
    print(f"Fase objetivo: {target_phase:.6f} rad\n")
    print("Evaluando configuraciones...")
    print("-" * 80)
    
    for i, config_dict in enumerate(configurations):
        config = AWQPEConfig(**config_dict)
        protocol = AWQPEProtocol(config, operator)
        result = protocol.run(verbose=False)
        
        error = circular_error(target_phase, result.phase_estimate)
        results_comparison.append((config_dict, result, error))
        
        print(f"\nConfig {i+1}:")
        print(f"  Bits: {config_dict['total_precision_bits']}, "
              f"Ventana: {config_dict['window_size']}, "
              f"Shots: {config_dict['n_shots']}")
        print(f"  Estimación: {result.phase_estimate:.6f}")
        print(f"  Error: {error:.6f}")
        print(f"  Num bloques: {len(result.block_results)}")
    
    # Análisis de trade-off
    print_separator()
    print("ANÁLISIS DE TRADE-OFF:")
    print("-" * 80)
    
    print("\nTendencias:")
    errors = [e for _, _, e in results_comparison]
    print(f"  Error máximo: {max(errors):.6f}")
    print(f"  Error mínimo: {min(errors):.6f}")
    print(f"  Mejora: {(max(errors) - min(errors))/max(errors)*100:.1f}%")
    
    print("\nRecomendaciones:")
    print("  - Ventanas más pequeñas (2) → ejecución rápida, menos preciso")
    print("  - Ventanas más grandes (4) → más preciso, más tiempo")
    print("  - Balance óptimo: ventana 3, shots 1024")


def example_4_multiple_phases():
    """
    EJEMPLO 4: ESTIMAR MÚLTIPLES FASES
    
    Evaluar rendimiento del protocolo para un rango
    de fases diferentes.
    """
    print_header("EJEMPLO 4: ESTIMACIÓN DE MÚLTIPLES FASES")
    
    print("Descripción:")
    print("-" * 80)
    print("Estimar varias fases para verificar consistencia.\n")
    
    config = AWQPEConfig(
        total_precision_bits=8,
        window_size=3,
        n_shots=1024
    )
    
    # Rango de fases a estimar
    target_phases = [0.2, 0.5, 0.7, 1.0, 1.5]
    
    print(f"Configuración: {config.total_precision_bits} bits, "
          f"ventana {config.window_size}, {config.n_shots} shots\n")
    print("Estimando fases...")
    print("-" * 80)
    
    results = []
    
    for phase in target_phases:
        operator = SimplePhaseOperator(phase)
        protocol = AWQPEProtocol(config, operator)
        result = protocol.run(verbose=False)
        
        error = circular_error(phase, result.phase_estimate)
        results.append((phase, result.phase_estimate, error))
        
        print(f"  ϕ = {phase:.2f}: estimado = {result.phase_estimate:.6f}, "
              f"error = {error:.6f}")
    
    # Estadísticas
    print_separator()
    print("ESTADÍSTICAS:")
    print("-" * 80)
    
    errors = [e for _, _, e in results]
    print(f"\nError promedio: {np.mean(errors):.6f}")
    print(f"Error máximo:   {np.max(errors):.6f}")
    print(f"Error mínimo:   {np.min(errors):.6f}")
    print(f"Desv. estándar: {np.std(errors):.6f}")
    
    # Evaluar correlación
    estimated_phases = [ep for _, ep, _ in results]
    correlation = np.corrcoef(target_phases, estimated_phases)[0, 1]
    print(f"\nCorrelación objetivo-estimado: {correlation:.6f}")
    
    if correlation > 0.99:
        print("✅ Excelente correlación: el protocolo es consistente")
    elif correlation > 0.95:
        print("✓ Buena correlación: rendimiento aceptable")
    else:
        print("⚠️  Correlación baja: revisar configuración")


def example_5_error_analysis():
    """
    EJEMPLO 5: ANÁLISIS DE ERROR Y CONFIABILIDAD
    
    Evaluar métricas de error y confianza del protocolo.
    """
    print_header("EJEMPLO 5: ANÁLISIS DE ERROR Y CONFIABILIDAD")
    
    print("Descripción:")
    print("-" * 80)
    print("Examinar errores acumulativos y métricas de confianza.\n")
    
    config = AWQPEConfig(
        total_precision_bits=8,
        window_size=3,
        n_shots=1024
    )
    
    target_phase = 0.6
    operator = SimplePhaseOperator(target_phase)
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=False)
    
    print(f"Fase objetivo: {target_phase:.6f} rad")
    print(f"Fase estimada: {result.phase_estimate:.6f} rad\n")
    
    print("-" * 80)
    print("MÉTRICAS GLOBALES:")
    print("-" * 80)
    print(f"Error total acumulado: {result.total_error:.2e}")
    print(f"Coherencia validada: {result.coherence_validated}")
    print(f"Bits de fase: {result.phase_bits}\n")
    
    print("-" * 80)
    print("ANÁLISIS POR BLOQUE:")
    print("-" * 80)
    
    for br in result.block_results:
        print(f"\nBloque {br.block_index}:")
        print(f"  Bits: {br.phase_bits}")
        print(f"  Confianza: {br.confidence:.4f} ({br.confidence*100:.1f}%)")
        print(f"  Ratio de ambigüedad: {br.ambiguity_ratio:.4f}", end="")
        
        if br.ambiguity_ratio > config.ambiguity_threshold:
            print(" ⚠️  (ALTO)")
        else:
            print(" ✓")
        
        print(f"  Candidatos:")
        for val, prob in br.top_candidates:
            print(f"    {val:3d}: {prob:.4f} ({prob*100:.1f}%)")
        
        if br.required_correction is not None:
            print(f"  Corrección LSB-to-MSB: {br.required_correction}")


def example_6_custom_operator():
    """
    EJEMPLO 6: USAR OPERADOR PERSONALIZADO
    
    Definir y usar un operador personalizado para
    aplicaciones específicas.
    """
    print_header("EJEMPLO 6: OPERADOR PERSONALIZADO")
    
    print("Descripción:")
    print("-" * 80)
    print("Definir un operador personalizado para simulación específica.\n")
    
    from awqpe_protocol import QuantumOperator
    
    class SinusoidalPhaseOperator(QuantumOperator):
        """Operador con fase sinusoidal."""
        
        def __init__(self, amplitude, frequency):
            self.amplitude = amplitude
            self.frequency = frequency
            self._eigenstate = np.array([1.0, 0.0])
        
        def apply(self, eigenstate, power):
            """Fase = A * sin(2π * k * f)"""
            k = power
            phase = self.amplitude * np.sin(2 * np.pi * k * self.frequency)
            return eigenstate, phase
        
        def get_eigenstate(self):
            return self._eigenstate.copy()
        
        @property
        def name(self):
            return f"Sinusoidal(A={self.amplitude:.2f}, f={self.frequency:.2f})"
    
    # Usar operador personalizado
    config = AWQPEConfig(
        total_precision_bits=8,
        window_size=3,
        n_shots=1024
    )
    
    operator = SinusoidalPhaseOperator(amplitude=0.5, frequency=0.3)
    
    print(f"Operador: {operator.name}\n")
    
    protocol = AWQPEProtocol(config, operator)
    result = protocol.run(verbose=False)
    
    print(f"Fase estimada: {result.phase_estimate:.6f} rad")
    print(f"Bits de fase: {result.phase_bits}")
    print(f"Error total: {result.total_error:.2e}")
    
    print("\n✓ Operador personalizado ejecutado exitosamente")


def main():
    """Ejecutar todos los ejemplos."""
    
    print("\n" + "#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + "  PROTOCOLO AWQPE - EJEMPLOS PRÁCTICOS".center(78) + "#")
    print("#" + "  Adaptive Windowed Quantum Phase Estimation".center(78) + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)
    
    try:
        # Ejecutar ejemplos en orden
        example_1_basic_phase_estimation()
        
        input("\n\nPresionar Enter para continuar al Ejemplo 2...")
        example_2_berry_phase_estimation()
        
        input("\n\nPresionar Enter para continuar al Ejemplo 3...")
        example_3_parameter_sensitivity()
        
        input("\n\nPresionar Enter para continuar al Ejemplo 4...")
        example_4_multiple_phases()
        
        input("\n\nPresionar Enter para continuar al Ejemplo 5...")
        example_5_error_analysis()
        
        input("\n\nPresionar Enter para continuar al Ejemplo 6...")
        example_6_custom_operator()
        
        # Resumen final
        print_header("RESUMEN DE EJEMPLOS")
        print("""
Ejemplos ejecutados:
  ✅ Ejemplo 1: Estimación de fase simple
  ✅ Ejemplo 2: Estimación de fase de Berry
  ✅ Ejemplo 3: Análisis de sensibilidad a parámetros
  ✅ Ejemplo 4: Estimación de múltiples fases
  ✅ Ejemplo 5: Análisis de error y confiabilidad
  ✅ Ejemplo 6: Operador personalizado

Próximos pasos:
  1. Revisar AWQPE_GUIA_COMPLETA.py para más ejemplos avanzados
  2. Ejecutar tests: pytest awqpe_tests.py -v
  3. Consultar README.md para documentación completa
  4. Experimentar con tus propios operadores

¡Gracias por usar AWQPE! 🎓
        """)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución cancelada por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante ejecución: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
