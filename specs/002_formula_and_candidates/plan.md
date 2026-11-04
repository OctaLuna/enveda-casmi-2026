# Plan de Implementación Técnica: 002_formula_and_candidates
## Arquitectura del Estimador de Fórmula, Filtros de Senior y Base de Candidatos

> **ID de Plan**: `PLAN-002`  
> **Feature**: Estimador de Fórmulas y Universo de Candidatos (Pilar B)  
> **Estado**: Listo para Construcción  

---

## 1. Arquitectura de Flujo Químico

```
[ Precursor m/z + Adduct ]
            |
            v
[ src/data/adduct_normalizer.py ]  -->  Masa Neutra Exacta M
            |
            v
[ src/data/formula_estimator.py ]
   |-- Descomposición combinatorial CHNOPS (+ Halógenos F, Cl, Br, I)
   |-- Filtrado por ventana de masa (ppm <= 5.0 - 10.0)
            |
            v
[ src/data/chemical_filters.py ]
   |-- Teorema de Valencia de Senior (Reglas 1, 2 y 3)
   |-- Grado de Insaturación DBE >= 0 (Capa cerrada neutra)
   |-- Ratios elementales de consistencia química (H/C, O/C, N/C)
            |
            v
[ Lista Ordenada de Fórmulas Candidatas ] (con Delta ppm y score de confianza)
            |
            v
[ src/data/candidate_db.py ]  <-- Indice offline O(1) de PubChem/COCONUT/LOTUS/HMDB
            |
            v
[ Candidatos Estructurales (SMILES + InChIKey14) para Pilar B (MIST/Tanimoto) ]
```

---

## 2. Modelos de Datos y Clases Clave

### 2.1 Restricciones Químicas (`src/data/chemical_filters.py`)
- `check_senior_rules(counts: dict[str, int]) -> tuple[bool, str]`:
  - Regla 1: $\sum v_i \ge 2 \cdot \max(v_i)$.
  - Regla 2: La cantidad de átomos con valencia impar es par (regla del nitrógeno extendida).
  - Regla 3: $\sum v_i \ge 2 \cdot (n - 1)$, donde $n = \sum \text{átomos}$.
- `calculate_dbe(counts: dict[str, int]) -> tuple[float, bool]`:
  - $DBE = C + 1 - \frac{H}{2} + \frac{N}{2} + \frac{P}{2} - \frac{X}{2}$ (donde $X = F + Cl + Br + I$).
  - Válido si $DBE \ge 0$ y $2 \cdot DBE$ es entero par.
- `check_elemental_ratios(counts: dict[str, int]) -> bool`:
  - $0.1 \le H/C \le 3.0$
  - $O/C \le 1.2$
  - $N/C \le 0.6$

### 2.2 Estimación de Fórmulas (`src/data/formula_estimator.py`)
- `CandidateFormula`:
  - `formula`: str (notación Hill, ej: "C8H10N4O2")
  - `counts`: dict[str, int]
  - `exact_mass`: float
  - `ppm_error`: float
  - `dbe`: float
  - `confidence_score`: float (0.0 a 1.0)
- `FormulaEstimator`:
  - `estimate_formulas(neutral_mass: float, ppm_tolerance: float = 7.0, allow_halogens: bool = False) -> list[CandidateFormula]`

### 2.3 Base de Candidatos (`src/data/candidate_db.py`)
- `CandidateRecord`:
  - `inchikey14`: str
  - `smiles`: str
  - `formula`: str
  - `sources`: list[str] (ej: ["PubChem", "COCONUT", "LOTUS"])
- `CandidateDatabase`:
  - `add_candidate(smiles: str, sources: list[str] = None)`
  - `get_candidates(formula: str) -> list[CandidateRecord]`
  - `save_to_parquet(path: Path)` / `load_from_parquet(path: Path)`

---

## 3. Estrategia de Pruebas y Validación TDD

- `tests/test_chemical_filters.py`:
  - Pruebas para moléculas neutras válidas (cafeína, glucosa, ácido acetilsalicílico).
  - Pruebas para fórmulas imposibles (ej. $CH_5$, $C_2H_7$, radicales con valencia impar, $DBE < 0$).
- `tests/test_formula_estimator.py`:
  - Estimación a partir de masa neutra teórica y masas reales de productos naturales conocidos.
  - Verificación de ordenamiento por $\Delta\text{ppm}$.
- `tests/test_candidate_db.py`:
  - Inserción y consulta $O(1)$ por fórmula Hill.
  - Deduplicación por `InChIKey14` fusionando listas de fuentes.
