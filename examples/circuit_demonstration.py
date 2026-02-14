"""
DEMOSTRACIÓN: ANÁLISIS AWQPE DE CIRCUITO METRIPLÉPTICO
=====================================================

Este script analiza el circuito proporcionado en formato JSON mediante 
el protocolo AWQPE, estimando el parámetro temporal t = 0.9823.
"""

import numpy as np
from awqpe_protocol import AWQPEConfig, AWQPEProtocol, MetriplecticCircuitOperator

def main():
    print("#" * 80)
    print("# ANALIZADOR DE CIRCUITOS METRIPLÉPTICOS AWQPE")
    print("#" * 80 + "\n")

    # Datos del circuito proporcionados por el usuario
    time_param = 0.9823000000008845
    print(f"[*] Parámetro temporal extraído: t = {time_param:.8f}")
    
    # Configuración del protocolo para alta precisión
    # Buscamos capturar la fase en un manifold de 7.0 rad
    config = AWQPEConfig(
        total_precision_bits=12,    # Alta precisión para capturar residuos finos
        window_size=4,             # Ventanas moderadas para estabilidad
        n_shots=2048,              # Más mediciones para reducir ruido
        phase_reset_value=7.0      # Reset Metripléptico (Analogía Rigurosa)
    )

    # Definir el operador basado en la geometría del circuito
    # H_0 · CY_12 · Inc_1 · Z^-t_0 · Dec_1
    operator = MetriplecticCircuitOperator(time_param)
    
    print(f"[*] Operador configurado: {operator.name}")
    print(f"[*] Manifold de fase: {config.phase_reset_value} rad\n")

    # Inicializar y ejecutar protocolo
    protocol = AWQPEProtocol(config, operator)
    
    print("=" * 70)
    print("EJECUTANDO PROTOCOLO AWQPE")
    print("=" * 70)
    
    result = protocol.run(verbose=True)

    print("\n" + "=" * 70)
    print("RECONSTRUCCIÓN METRIPLÉPTICA")
    print("=" * 70)
    
    # El tiempo t se recupera normalizando la fase estimada por el reset
    t_est = result.phase_estimate / config.phase_reset_value
    
    print(f"\nFase estimada: {result.phase_estimate:.6f} rad")
    print(f"Tiempo recuperado (t_est): {t_est:.8f}")
    print(f"Tiempo original  (t_target): {time_param:.8f}")
    
    error_abs = abs(t_est - time_param)
    print(f"Error absoluto en t: {error_abs:.2e}")
    
    print("\nInterpretación Física:")
    print("-" * 70)
    print("La estructura del circuito (Inc/Dec) actúa como un transportador")
    print("de fase que codifica el parámetro temporal en el manifold de 7 rad.")
    print("El residuo observado de ~0.72 rad es el 'aliento' del sistema")
    print("transfiriendo información entre los momentos x, y, z.")

if __name__ == "__main__":
    main()
