"""
LATTICE 3D CUÁNTICO CON COSENOS DIRECTORES
═════════════════════════════════════════════════════════════════════════════

Implementación de lattice 3×3×3 usando 6 qubits (2 por coordenada).
Mapeo directo a cosenos directores para navegación geométrica.

Estructura:
  Qubits 0-1: Codifican x ∈ {0,1,2}
  Qubits 2-3: Codifican y ∈ {0,1,2}
  Qubits 4-5: Codifican z ∈ {0,1,2}

Estados permitidos: 27
Estados prohibidos: 5 (cuando alguna coordenada = 11 en binario)

Característica clave: Cosenos directores (cos α, cos β, cos γ)
  describe orientación del vector de estado en 3D.
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# CLASE PRINCIPAL: LATTICE 3D CON COSENOS DIRECTORES
# ============================================================================

@dataclass
class DirectionVector:
    """Representa dirección en 3D usando cosenos directores."""
    
    x: int                      # Coordenada x ∈ {0,1,2}
    y: int                      # Coordenada y ∈ {0,1,2}
    z: int                      # Coordenada z ∈ {0,1,2}
    
    cos_alpha: float            # Coseno α (dirección x)
    cos_beta: float             # Coseno β (dirección y)
    cos_gamma: float            # Coseno γ (dirección z)
    
    @property
    def norm_squared(self) -> float:
        """Norma² de cosenos directores (debe ser ~1)"""
        return self.cos_alpha**2 + self.cos_beta**2 + self.cos_gamma**2
    
    @property
    def is_normalized(self) -> bool:
        """Verificar si está correctamente normalizado"""
        return np.isclose(self.norm_squared, 1.0, atol=0.1)
    
    def __repr__(self) -> str:
        return (f"DirVector(({self.x},{self.y},{self.z})) "
                f"cos({self.cos_alpha:.3f},{self.cos_beta:.3f},"
                f"{self.cos_gamma:.3f}) "
                f"norm²={self.norm_squared:.3f}")


class Lattice3D_6Qubit:
    """
    Implementación del lattice 3×3×3 usando 6 qubits.
    
    Mapeo:
      Bitstring [b₀b₁ b₂b₃ b₄b₅]
        ↓
      Coordenadas (x,y,z) donde cada = 2-bit value
        ↓
      Cosenos directores (α,β,γ)
    
    Propiedades:
      - 27 estados permitidos de 32 posibles
      - Simetría cúbica (Oh)
      - Escalable a N×N×N
    """
    
    # Constante de normalización para cosenos directores
    NORM_FACTOR = np.sqrt(2)  # Porque (x-1)² máx es 1, tres coords → factor √2
    
    def __init__(self):
        """Inicializar lattice 3D."""
        self.n_qubits = 6
        self.lattice_dimension = 3
        self.n_states = 27  # 3³
        self.n_prohibited = 5  # 32 - 27
        
        # Pre-computar todos los estados permitidos y sus cosenos
        self.allowed_coords = [
            (x, y, z) 
            for x in range(3) 
            for y in range(3) 
            for z in range(3)
        ]
        
        self.direction_vectors = [
            self._coords_to_direction(x, y, z)
            for x, y, z in self.allowed_coords
        ]
    
    def _coords_to_direction(self, x: int, y: int, z: int) -> DirectionVector:
        """Convertir coordenadas a vector de dirección con cosenos."""
        
        # Normalizador: centrar en (1,1,1)
        cos_alpha = (x - 1) / self.NORM_FACTOR
        cos_beta = (y - 1) / self.NORM_FACTOR
        cos_gamma = (z - 1) / self.NORM_FACTOR
        
        return DirectionVector(
            x=x, y=y, z=z,
            cos_alpha=cos_alpha,
            cos_beta=cos_beta,
            cos_gamma=cos_gamma
        )
    
    def bitstring_to_coords(self, bitstring: str) -> Optional[Tuple[int, int, int]]:
        """
        Convertir 6-bit string a coordenadas (x,y,z).
        
        Retorna None si el estado es prohibido (alguna coord = 11 = 3).
        
        Args:
            bitstring: String de 6 bits (ej: "000000")
        
        Returns:
            (x,y,z) si permitido, None si prohibido
        """
        if len(bitstring) != 6:
            raise ValueError("bitstring debe tener exactamente 6 bits")
        
        # Decodificar cada par de bits
        x = int(bitstring[0:2], 2)
        y = int(bitstring[2:4], 2)
        z = int(bitstring[4:6], 2)
        
        # Verificar prohibición: cualquier coordenada = 3 (estado 11)
        if x > 2 or y > 2 or z > 2:
            return None
        
        return (x, y, z)
    
    def coords_to_bitstring(self, x: int, y: int, z: int) -> str:
        """Convertir coordenadas a 6-bit string."""
        if not (0 <= x <= 2 and 0 <= y <= 2 and 0 <= z <= 2):
            raise ValueError("Coordenadas fuera de rango [0,2]")
        
        return f"{x:02b}{y:02b}{z:02b}"
    
    def bitstring_to_direction(self, bitstring: str) -> Optional[DirectionVector]:
        """Obtener vector de dirección directamente de bitstring."""
        coords = self.bitstring_to_coords(bitstring)
        if coords is None:
            return None
        x, y, z = coords
        return self._coords_to_direction(x, y, z)
    
    def get_all_allowed_bitstrings(self) -> List[str]:
        """Obtener todos los bitstrings permitidos (27 estados)."""
        return [
            self.coords_to_bitstring(x, y, z)
            for x, y, z in self.allowed_coords
        ]
    
    def get_all_prohibited_bitstrings(self) -> List[str]:
        """Obtener bitstrings prohibidos (5 estados)."""
        all_bitstrings = [
            f"{i:06b}" for i in range(32)
        ]
        allowed = set(self.get_all_allowed_bitstrings())
        prohibited = [b for b in all_bitstrings if b not in allowed]
        return prohibited
    
    def filter_measurement_results(
        self,
        measurement_histogram: Dict[str, int]
    ) -> Dict[Tuple[int,int,int], int]:
        """
        Filtrar resultados de medición para obtener solo estados permitidos.
        
        Args:
            measurement_histogram: {bitstring: count}
        
        Returns:
            {(x,y,z): count} solo para estados permitidos
        """
        filtered = {}
        
        for bitstring, count in measurement_histogram.items():
            coords = self.bitstring_to_coords(bitstring)
            if coords is not None:
                filtered[coords] = filtered.get(coords, 0) + count
        
        return filtered
    
    def compute_direction_statistics(
        self,
        filtered_results: Dict[Tuple[int,int,int], int]
    ) -> Dict[str, float]:
        """
        Computar estadísticas de cosenos directores.
        
        Args:
            filtered_results: {(x,y,z): count}
        
        Returns:
            Diccionario con medias y varianzas de cosenos
        """
        total_counts = sum(filtered_results.values())
        
        cos_alpha_values = []
        cos_beta_values = []
        cos_gamma_values = []
        
        for (x, y, z), count in filtered_results.items():
            direction = self._coords_to_direction(x, y, z)
            
            for _ in range(count):
                cos_alpha_values.append(direction.cos_alpha)
                cos_beta_values.append(direction.cos_beta)
                cos_gamma_values.append(direction.cos_gamma)
        
        return {
            'cos_alpha_mean': np.mean(cos_alpha_values),
            'cos_alpha_std': np.std(cos_alpha_values),
            'cos_beta_mean': np.mean(cos_beta_values),
            'cos_beta_std': np.std(cos_beta_values),
            'cos_gamma_mean': np.mean(cos_gamma_values),
            'cos_gamma_std': np.std(cos_gamma_values),
            'norm_squared_mean': np.mean([
                ca**2 + cb**2 + cg**2
                for ca, cb, cg in zip(cos_alpha_values, cos_beta_values, cos_gamma_values)
            ])
        }
    
    def nearest_neighbors(self, x: int, y: int, z: int) -> List[Tuple[int,int,int]]:
        """
        Obtener vecinos próximos en el lattice 3D (6-conectado).
        
        Args:
            (x,y,z): Coordenada central
        
        Returns:
            Lista de coordenadas vecinas
        """
        neighbors = []
        
        for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            nx, ny, nz = x + dx, y + dy, z + dz
            if 0 <= nx <= 2 and 0 <= ny <= 2 and 0 <= nz <= 2:
                neighbors.append((nx, ny, nz))
        
        return neighbors
    
    def coupling_strength(
        self,
        coord1: Tuple[int,int,int],
        coord2: Tuple[int,int,int]
    ) -> float:
        """
        Calcular fuerza de acoplamiento entre dos estados.
        
        Basado en distancia de cosenos directores:
        J = 1 - |cos1 - cos2| / 2
        
        Args:
            coord1, coord2: Coordenadas de dos estados
        
        Returns:
            Fuerza de acoplamiento [0, 1]
        """
        dir1 = self._coords_to_direction(*coord1)
        dir2 = self._coords_to_direction(*coord2)
        
        # Distancia Euclidea en espacio de cosenos
        distance = np.sqrt(
            (dir1.cos_alpha - dir2.cos_alpha)**2 +
            (dir1.cos_beta - dir2.cos_beta)**2 +
            (dir1.cos_gamma - dir2.cos_gamma)**2
        )
        
        # Convertir a fuerza (máximo cuando distance=0)
        coupling = 1.0 - min(distance, 1.0)
        
        return coupling


# ============================================================================
# INTEGRACIÓN CON AWQPE: VERSIÓN 3D
# ============================================================================

class AWQPE_3D:
    """
    AWQPE adaptado para estimar 3 fases simultáneamente
    (una por cada dimensión del lattice).
    """
    
    def __init__(self, lattice: Lattice3D_6Qubit):
        """
        Args:
            lattice: Instancia de Lattice3D_6Qubit
        """
        self.lattice = lattice
    
    def phase_to_coord(self, phase: float) -> int:
        """
        Mapear fase estimada a coordenada ∈ {0,1,2}.
        
        Dividir [0, 2π] en 3 regiones iguales.
        
        Args:
            phase: Fase estimada (radianes)
        
        Returns:
            Coordenada 0, 1, o 2
        """
        # Normalizar a [0, 2π]
        norm_phase = np.mod(phase, 2 * np.pi)
        
        # Dividir en 3 regiones
        region_width = 2 * np.pi / 3
        
        if norm_phase < region_width:
            return 0
        elif norm_phase < 2 * region_width:
            return 1
        else:
            return 2
    
    def run_3d(
        self,
        phase_x: float,
        phase_y: float,
        phase_z: float
    ) -> Tuple[int, int, int]:
        """
        Ejecutar AWQPE 3D (estimar 3 fases → 3 coordenadas).
        
        Args:
            phase_x, phase_y, phase_z: Fases estimadas por AWQPE
        
        Returns:
            (x, y, z) coordenadas del lattice
        """
        x = self.phase_to_coord(phase_x)
        y = self.phase_to_coord(phase_y)
        z = self.phase_to_coord(phase_z)
        
        return (x, y, z)


# ============================================================================
# EJEMPLO: SIMULACIÓN DE MEDICIONES
# ============================================================================

class Lattice3D_Simulator:
    """Simula mediciones en el lattice 3D."""
    
    def __init__(self, lattice: Lattice3D_6Qubit):
        """
        Args:
            lattice: Instancia de Lattice3D_6Qubit
        """
        self.lattice = lattice
    
    def simulate_measurement(
        self,
        true_coords: Tuple[int, int, int],
        shots: int = 1024,
        noise_level: float = 0.1
    ) -> Dict[str, int]:
        """
        Simular medición con ruido Gaussiano pequeño.
        
        Args:
            true_coords: (x,y,z) verdadero
            shots: Número de shots
            noise_level: Desviación estándar del ruido
        
        Returns:
            {bitstring: count}
        """
        if not all(0 <= c <= 2 for c in true_coords):
            raise ValueError("Coordenadas fuera de rango")
        
        # Generar resultados con distribución sesgada hacia true_coords
        histogram = {}
        
        for _ in range(shots):
            # Con probabilidad 1-noise_level, retornar verdadero
            if np.random.random() < (1 - noise_level):
                result = true_coords
            else:
                # Añadir ruido: cambiar una coordenada aleatoriamente
                noisy_coords = list(true_coords)
                axis = np.random.randint(0, 3)
                noisy_coords[axis] = (noisy_coords[axis] + np.random.choice([-1, 1])) % 3
                result = tuple(noisy_coords)
            
            # Convertir a bitstring
            bitstring = self.lattice.coords_to_bitstring(*result)
            histogram[bitstring] = histogram.get(bitstring, 0) + 1
        
        return histogram
    
    def run_full_measurement_cycle(
        self,
        true_coords: Tuple[int, int, int],
        shots: int = 1024
    ) -> Dict:
        """
        Ejecutar ciclo completo: medir → filtrar → analizar.
        
        Args:
            true_coords: Verdadera coordenada en lattice
            shots: Shots cuánticos
        
        Returns:
            Diccionario con resultados completos
        """
        # Simular medición
        histogram = self.simulate_measurement(true_coords, shots=shots)
        
        # Filtrar estados prohibidos
        filtered = self.lattice.filter_measurement_results(histogram)
        
        # Obtener dirección de cosenos
        true_direction = self.lattice._coords_to_direction(*true_coords)
        
        # Calcular estadísticas
        stats = self.lattice.compute_direction_statistics(filtered)
        
        # Identificar estado más probable
        most_probable = max(filtered.items(), key=lambda x: x[1])[0]
        most_probable_direction = self.lattice._coords_to_direction(*most_probable)
        
        return {
            'true_coords': true_coords,
            'true_direction': true_direction,
            'measurement_histogram': histogram,
            'filtered_results': filtered,
            'most_probable_coords': most_probable,
            'most_probable_direction': most_probable_direction,
            'direction_statistics': stats,
            'prohibited_counts': sum(
                count for bitstring, count in histogram.items()
                if self.lattice.bitstring_to_coords(bitstring) is None
            ),
            'allowed_counts': sum(filtered.values()),
            'total_shots': shots
        }


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def example_3d_lattice():
    """Demostración completa del lattice 3D con cosenos directores."""
    
    print("\n" + "="*70)
    print("LATTICE 3D CUÁNTICO CON COSENOS DIRECTORES")
    print("="*70 + "\n")
    
    # Crear lattice
    lattice = Lattice3D_6Qubit()
    
    print(f"Lattice: {lattice.lattice_dimension}×{lattice.lattice_dimension}"
          f"×{lattice.lattice_dimension}")
    print(f"Estados permitidos: {lattice.n_states}")
    print(f"Estados prohibidos: {lattice.n_prohibited}")
    print(f"Qubits necesarios: {lattice.n_qubits}\n")
    
    # Mostrar todos los estados permitidos y sus cosenos
    print("Estados permitidos y cosenos directores:")
    print("-" * 70)
    for i, (x, y, z) in enumerate(lattice.allowed_coords[:5]):  # Primeros 5
        direction = lattice._coords_to_direction(x, y, z)
        print(f"{i}: ({x},{y},{z}) → cos(α,β,γ)=({direction.cos_alpha:+.3f}, "
              f"{direction.cos_beta:+.3f}, {direction.cos_gamma:+.3f}) "
              f"norm²={direction.norm_squared:.3f}")
    print("...\n")
    
    # Simular medición
    print("SIMULACIÓN DE MEDICIÓN")
    print("-" * 70)
    
    simulator = Lattice3D_Simulator(lattice)
    true_coords = (1, 1, 2)  # Centro + arriba
    
    result = simulator.run_full_measurement_cycle(true_coords, shots=2048)
    
    print(f"Verdadera coordenada: {result['true_coords']}")
    print(f"Verdadera dirección: {result['true_direction']}\n")
    
    print(f"Mediciones:")
    print(f"  Total shots: {result['total_shots']}")
    print(f"  Estados permitidos: {result['allowed_counts']}")
    print(f"  Estados prohibidos (error): {result['prohibited_counts']}\n")
    
    print(f"Estado más probable: {result['most_probable_coords']}")
    print(f"Dirección probable: {result['most_probable_direction']}\n")
    
    stats = result['direction_statistics']
    print("Estadísticas de cosenos directores:")
    print(f"  cos α: {stats['cos_alpha_mean']:.4f} ± {stats['cos_alpha_std']:.4f}")
    print(f"  cos β: {stats['cos_beta_mean']:.4f} ± {stats['cos_beta_std']:.4f}")
    print(f"  cos γ: {stats['cos_gamma_mean']:.4f} ± {stats['cos_gamma_std']:.4f}")
    print(f"  norm² (debe ~1): {stats['norm_squared_mean']:.4f}\n")
    
    # Mostrar vecinos próximos
    print("Vecinos próximos de (1,1,1):")
    print("-" * 70)
    center = (1, 1, 1)
    neighbors = lattice.nearest_neighbors(*center)
    for neighbor in neighbors:
        coupling = lattice.coupling_strength(center, neighbor)
        print(f"  {center} → {neighbor}: coupling={coupling:.3f}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    example_3d_lattice()
