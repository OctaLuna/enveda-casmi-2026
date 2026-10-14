# Skill: Data Validator
**Path**: `.agents/skills/data-validator.md`  
**Purpose**: Procedimiento estandarizado y agnóstico para auditar, verificar y validar la calidad de datasets químicos y espectrales en el proyecto CASMI 2026.

---

## 1. Alcance de Validación
Esta skill debe ejecutarse cada vez que:
- Se incorpore una nueva partición o archivo (`train.parquet`, `test.parquet`, splits locales).
- Se realice una transformación de datos (deisotopado, normalización de intensidades, corrección de aductos).
- Se generen o actualicen los subsets de validación local (Val-Clase1, Val-Clase2, Val-Clase3).

---

## 2. Protocolo de Auditoría Espectral & Químico

### 2.1 Integridad Estructural y Formatos
- [ ] **Esquema de Columnas**: Verificar presencia obligatoria de:
  - `molecule_id` (str o int identificador unívoco de la sustancia)
  - `spectrum_id` (str identificador unívoco de la adquisición espectral)
  - `ms2_mzs` (array de floats con masas fragmentadas $m/z$)
  - `ms2_normalized_intensities` (array de floats normalizados, pico base = 1.0)
  - `precursor_mz` (float > 0)
  - `adduct` (str indicando modo de ionización: `[M+H]+`, `[M-H]-`, etc.)
  - `collision_energy_ev` (float / int)
  - `label` (str SMILES canónico, solo en train)
- [ ] **Longitudes Paritarias**: Comprobar rigurosamente que `len(ms2_mzs) == len(ms2_normalized_intensities)` para cada fila.
- [ ] **Valores Nulos / Corruptos**:
  - Cero NaNs, nulls o infinitos en arreglos de picos y precursores.
  - Eliminar espectros con menos de 5 picos informativos (`len(peaks) >= 5`).

### 2.2 Validación de Parámetros Físico-Químicos
- [ ] **Filtro de Precursor**: Ningún pico de fragmento puede exceder `precursor_mz + 2.0 Da` (tolerancia isotópica).
- [ ] **Cálculo de Masa Neutra**:
  - Verificar que la masa neutra derivada del `adduct` sea físicamente viable ($100 < M_{neutra} < 2000$ Da para metabolitos pequeños).
- [ ] **Canonicalización SMILES**:
  - Todos los SMILES de train deben pasar la validación de RDKit (`Chem.MolFromSmiles(smiles) is not None`).
  - Generar y verificar `InChIKey14` para cada molécula sin excepciones.

### 2.3 Auditoría de Particiones y Prevención de Fugas (Data Leakage)
- [ ] **Disjunción Estricta por `molecule_id`**:
  $$\text{Set}(\text{train\_molecule\_ids}) \cap \text{Set}(\text{val\_molecule\_ids}) = \emptyset$$
  $$\text{Set}(\text{train\_molecule\_ids}) \cap \text{Set}(\text{test\_molecule\_ids}) = \emptyset$$
- [ ] **Clustering Estructural**:
  - Ningún scaffold de Murcko idéntico debe coexistir entre Train y Val-Clase3.
  - La distancia MCES o similitud Tanimoto ECFP4 entre Val-Clase3 y Train debe ser $< 0.40$.
- [ ] **Data Drift**: Comparar histogramas de `precursor_mz` y distribuciones de aductos entre `train.parquet` y `test.parquet`.

---

## 3. Salida y Reporte
El validador debe emitir un log estructurado en formato JSON o Markdown que especifique:
- Total de filas analizadas y espectros descartados (con causa).
- Número de moléculas únicas y ratio de espectros por molécula.
- Verificación del hash de integridad de los archivos particionados.
