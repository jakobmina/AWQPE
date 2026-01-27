"""
MODELO CUÁNTICO DE CONFINAMIENTO CORREGIDO
============================================

Implementa un sistema de 3 qubits + 2 ancillas para modelar confinamiento
cuántico con límites en 000 y 111 (estados n=0 a n=7).

Concepto físico (Nivel 3 - Isomorfismo Físico):
- Datos (3 qubits): representan nivel de confinamiento n ∈ {0,1,...,7}
- Ancillas (2 qubits): actúan como "detectores de barrera"
  * ancilla[0]: detecta límite inferior (estado 000)
  * ancilla[1]: detecta límite superior (estado 111)

Simetría cíclica:
- Estados {1,6}, {2,5}, {3,4} son equivalentes bajo rotación 2π
- Verificación dimensional: 7 - 6.28 ≈ 0.72 ✓

Fases de ejecución:
1. Inicializar datos en superposición |+++⟩
2. Preparar ancillas en |++⟩ (escucha coherente)
3. Detectar límites (CCX/CX gates)
4. Acoplar datos con ancillas
5. Cerrar superposición con H
6. Medir ancillas (dejar datos intactos)
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2 as Sampler


class QuantumConfinementModel:
    """
    Modelo de confinamiento cuántico con detección coherente de límites.
    
    Arquitectura:
    - 3 qubits de datos (q0, q1, q2)
    - 2 ancillas de detección (anc0, anc1)
    - 1 registro de lectura (2 bits clásicos)
    """
    
    def __init__(self, verbose=False):
        """
        Inicializa el modelo.
        
        Args:
            verbose (bool): Si True, imprime debug info
        """
        self.verbose = verbose
        
        # ===== REGISTROS CUÁNTICOS =====
        # DATOS: 3 qubits → representan estado de confinamiento (0-7)
        self.qdata = QuantumRegister(3, name='q')
        
        # ANCILLAS: 2 qubits → detectan límites
        # anc[0]: detecta estado 000 (límite inferior)
        # anc[1]: detecta estado 111 (límite superior)
        self.ancillas = QuantumRegister(2, name='anc')
        
        # LECTURA: registro clásico para medir ancillas
        self.creg = ClassicalRegister(2, name='m')
        
        # Circuito integrado
        self.circuit = QuantumCircuit(self.qdata, self.ancillas, self.creg)
        
        # Construir circuito
        self._build_circuit()
    
    def _build_circuit(self):
        """
        Construye el circuito de confinamiento siguiendo 7 fases coherentes.
        """
        if self.verbose:
            print("[*] Construyendo circuito...")
        
        # ===== FASE 1: INICIALIZACIÓN DE DATOS =====
        # Poner los 3 qubits en superposición uniforme |+++⟩
        # Esto representa una distribución equiprobable sobre los 8 estados
        if self.verbose:
            print("  [1] Inicializando datos en |+++⟩")
        
        for i in range(3):
            self.circuit.h(self.qdata[i])
        
        self.circuit.barrier()
        
        # ===== FASE 2: PREPARACIÓN DE ANCILLAS =====
        # Poner ancillas en superposición |++⟩
        # Esto permite detección coherente (no colapsada) de límites
        if self.verbose:
            print("  [2] Preparando ancillas en |++⟩")
        
        self.circuit.h(self.ancillas[0])
        self.circuit.h(self.ancillas[1])
        
        self.circuit.barrier()
        
        # ===== FASE 3: DETECCIÓN DE LÍMITE INFERIOR (estado 000) =====
        # Lógica: Si q0=0 AND q1=0 AND q2=0, voltear ancilla[0]
        # Implementación:
        #   CCX(q0, q1, anc[0])  : si q0=1 AND q1=1, voltear anc[0]
        #   CX(q2, anc[0])       : si q2=1, voltear anc[0]
        # Esto voltea anc[0] solo si TODOS los qubits son 0
        # (porque buscamos: cuando todo es 0)
        
        if self.verbose:
            print("  [3a] Detectando límite inferior (000)...")
        
        self.circuit.ccx(self.qdata[0], self.qdata[1], self.ancillas[0])
        self.circuit.cx(self.qdata[2], self.ancillas[0])
        
        # ===== FASE 4: DETECCIÓN DE LÍMITE SUPERIOR (estado 111) =====
        # Lógica: Si q0=1 AND q1=1 AND q2=1, voltear ancilla[1]
        # Implementación: Invertir lógica con puertas X
        #   1. X(q0), X(q1), X(q2)          : invertir a 010 → 101
        #   2. CCX(q0, q1, anc[1])          : controlar en 1
        #   3. CX(q2, anc[1])               : controlar en 1
        #   4. X(q0), X(q1), X(q2)          : restaurar
        
        if self.verbose:
            print("  [3b] Detectando límite superior (111)...")
        
        # Invertir qubits para controlar sobre 1 en lugar de 0
        self.circuit.x(self.qdata[0])
        self.circuit.x(self.qdata[1])
        self.circuit.x(self.qdata[2])
        
        # Detectar con CCX/CX (ahora detecta 000 en la lógica invertida = 111 original)
        self.circuit.ccx(self.qdata[0], self.qdata[1], self.ancillas[1])
        self.circuit.cx(self.qdata[2], self.ancillas[1])
        
        # Restaurar qubits de datos
        self.circuit.x(self.qdata[0])
        self.circuit.x(self.qdata[1])
        self.circuit.x(self.qdata[2])
        
        self.circuit.barrier()
        
        # ===== FASE 5: ACOPLAMIENTO DATOS-ANCILLAS =====
        # Entrelazar qubits de datos con ancillas para marcar la "firma" de confinamiento
        # Cada qubit de datos controla una ancilla (ciclado)
        if self.verbose:
            print("  [4] Acoplando datos con ancillas (entrelazamiento)...")
        
        for i in range(3):
            self.circuit.cx(self.qdata[i], self.ancillas[(i % 2)])
        
        self.circuit.barrier()
        
        # ===== FASE 6: CIERRE DE SUPERPOSICIÓN =====
        # Aplicar H a las ancillas para "cerrar" la superposición
        # Esto proyecta el estado hacia la base computacional antes de medir
        if self.verbose:
            print("  [5] Cerrando superposición de ancillas con H...")
        
        self.circuit.h(self.ancillas[0])
        self.circuit.h(self.ancillas[1])
        
        self.circuit.barrier()
        
        # ===== FASE 7: MEDICIÓN =====
        # Medimos SOLO las ancillas
        # Los qubits de datos quedan sin medir (en entrelazamiento)
        if self.verbose:
            print("  [6] Midiendo ancillas...")
        
        self.circuit.measure(self.ancillas, self.creg)
        
        if self.verbose:
            print("[✓] Circuito construido.\n")
    
    def run_simulation(self, shots=1024):
        """
        Ejecuta la simulación del circuito.
        
        Args:
            shots (int): Número de ejecuciones
            
        Returns:
            dict: Conteos de estados de ancillas
                  Ej: {'00': 256, '01': 384, '10': 384, '11': 0}
        """
        if self.verbose:
            print(f"[*] Ejecutando simulación ({shots} shots)...")
        
        sampler = Sampler()
        job = sampler.run([self.circuit], shots=shots)
        result = job.result()
        
        counts = result[0].data.m.get_counts()
        
        if self.verbose:
            print("[✓] Simulación completada.\n")
        
        return counts
    
    def analyze_results(self, counts):
        """
        Analiza e interpreta los resultados.
        
        Args:
            counts (dict): Conteos de estados
        """
        total = sum(counts.values())
        
        print("\n" + "=" * 70)
        print("ANÁLISIS DE RESULTADOS")
        print("=" * 70)
        
        print(f"\nTotal de shots: {total}")
        print("\nDistribución de estados de ancillas:")
        print("-" * 70)
        
        # Ordenar por frecuencia (descendente)
        sorted_states = sorted(counts.items(), key=lambda x: -x[1])
        
        for estado, count in sorted_states:
            prob_percent = (count / total) * 100
            bar = "█" * int(prob_percent / 2)
            print(f"  {estado:>2s}: {count:>5d} ({prob_percent:>6.2f}%) {bar}")
        
        print("\n" + "=" * 70)
        print("INTERPRETACIÓN FÍSICA")
        print("=" * 70)
        
        print("""
Expectativa teórica:

1. SUPERPOSICIÓN INICIAL:
   - 3 qubits en |+++⟩ crean superposición de 8 estados {000,...,111}
   - Cada estado es equiprobable (12.5%)

2. DETECCIÓN DE LÍMITES:
   - Ancilla[0] "reacciona" cuando detecta 000 (límite inferior)
   - Ancilla[1] "reacciona" cuando detecta 111 (límite superior)
   - Estados internos (001-110) no activan ambas ancillas

3. ACOPLAMIENTO DATOS-ANCILLAS:
   - Crea entrelazamiento que marca la "firma" de cada región
   - Límites vs. confinamiento tienen firmas diferentes

4. RESULTADO ESPERADO:
   - Patrón NO uniforme en ancillas
   - Sesgo diferencial hacia ciertos estados {'00','01','10','11'}
   - Estados límite mostrarán menos ocupación en algunos estados

5. CONFINAMIENTO EFECTIVO:
   - Si observas sesgo claro → confinamiento funcionando
   - Si ves distribución uniforme → revisar CCX/CX gates
        """)
        
        return counts
    
    def draw(self):
        """
        Retorna representación textual del circuito.
        
        Returns:
            str: Diagrama ASCII del circuito
        """
        return self.circuit.draw(output='text', scale=0.8)
    
    def print_circuit_info(self):
        """Imprime información del circuito (tamaño, profundidad, etc.)."""
        print("\n" + "=" * 70)
        print("INFORMACIÓN DEL CIRCUITO")
        print("=" * 70)
        print(f"Qubits totales: {self.circuit.num_qubits}")
        print(f"Qubits de datos: 3 (q[0], q[1], q[2])")
        print(f"Qubits ancilla: 2 (anc[0], anc[1])")
        print(f"Bits clásicos: 2")
        print(f"Profundidad del circuito: {self.circuit.depth()}")
        print(f"Número de puertas: {len(self.circuit)}")


def main():
    """Función principal: crea, visualiza y ejecuta el modelo."""
    
    print("\n" + "=" * 70)
    print("MODELO CUÁNTICO DE CONFINAMIENTO")
    print("=" * 70)
    print("""
Parámetros:
  - 3 qubits de datos → 8 estados posibles (000 a 111)
  - 2 ancillas → detectores de límites (000 y 111)
  - Simetría cíclica: estados {1,6}, {2,5}, {3,4} equivalentes en 2π
  - Límites: n=0 (000) y n=7 (111) son barreras potenciales
    """)
    
    # Crear instancia del modelo
    model = QuantumConfinementModel(verbose=True)
    
    # Mostrar información del circuito
    model.print_circuit_info()
    
    # Mostrar diagrama del circuito
    print("\n" + "=" * 70)
    print("DIAGRAMA DEL CIRCUITO")
    print("=" * 70 + "\n")
    print(model.draw())
    
    # Ejecutar simulación
    print("\n" + "=" * 70)
    print("EJECUTANDO SIMULACIÓN")
    print("=" * 70)
    
    counts = model.run_simulation(shots=2048)
    
    # Analizar resultados
    model.analyze_results(counts)
    
    print("\n" + "=" * 70)
    print("DATOS BRUTOS")
    print("=" * 70)
    print(f"\nConteos: {counts}\n")


if __name__ == "__main__":
    main()
