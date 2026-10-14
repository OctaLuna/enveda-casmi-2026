# Skill: Code Reviewer
**Path**: `.agents/skills/code-reviewer.md`  
**Purpose**: Checklist exhaustivo para revisión de código, optimización de memoria/GPU, prevención de fuga de datos (data leakage) y calidad en el proyecto CASMI 2026.

---

## 1. Chemoinformatics & Mass Spectrometry Pitfalls
- [ ] **Canonicalización InChIKey14**: ¿Se utiliza la misma función de estandarización tautomérica con RDKit (`rdMolStandardize.TautomerEnumerator`)? ¿Se compara contra los primeros 14 caracteres del InChIKey?
- [ ] **Masa Neutra y Aductos**: ¿Se resta o suma la masa del aducto (`[M+H]+`, `[M+Na]+`, `[M-H]-`) antes de cualquier predicción o matching de fórmula elemental?
- [ ] **Tolerancia de Masa**: ¿Se aplican tolerancias adecuadas de espectrómetro Bruker timsTOF (5-10 ppm o 0.005 Da) al buscar fórmulas elementales?
- [ ] **Manipulación de SMILES**: ¿Se manejan adecuadamente SMILES inválidos con bloques `try/except` sin provocar caídas silenciosas o crashes del loop principal?

---

## 2. Prevención de Data Leakage y Split Integrity
- [ ] **Aislamiento por `molecule_id`**: ¿Se garantiza que ningún espectro perteneciente a una molécula en el conjunto de validación o test aparezca en el conjunto de entrenamiento?
- [ ] **Fuga Estructural (Clase 3)**: ¿El split para simular la Clase 3 utiliza agrupamiento por scaffold de Murcko o MCES y no un split puramente aleatorio?
- [ ] **Transformaciones Pre-Split**: ¿Las normalizaciones globales (ej. escalados o estadísticas de picos) se calcularon únicamente sobre el split de train y se aplicaron a validación/test sin recalculación?

---

## 3. Rendimiento, GPU y Memoria
- [ ] **Presupuesto Kaggle (< 9 horas)**: ¿La complejidad algorítmica permite procesar las ~400 moléculas del test set en cascada dentro del tiempo límite?
- [ ] **Fugas de Memoria en PyTorch**:
  - ¿Se usa `tensor.detach().item()` o `tensor.detach().cpu()` al acumular métricas o pérdidas?
  - ¿Se limpia la caché con `torch.cuda.empty_cache()` tras inferencias pesadas o batches de candidatos?
- [ ] **Vectorización con FAISS & NumPy**: ¿Las búsquedas de similitud o distancias espectrales están vectorizadas en lugar de utilizar loops Python puros `for i in range(...)`?

---

## 4. Pruebas y Cobertura (TDD)
- [ ] **Existencia de Tests**: ¿Todo nuevo método o clase en `src/` tiene una función de test correspondiente en `tests/`?
- [ ] **Casos de Borde (Edge Cases)**: ¿Se prueban espectros con pocos picos (<5), intensidades extremas, aductos atípicos y listas de predicciones vacías?
- [ ] **Determinismo**: ¿El test se ejecuta con una semilla fija y da un resultado determinista?

---

## 5. Estilo y Limpieza
- [ ] **Ruff & Black**: ¿El código pasa `ruff check` y está formateado con `black` sin errores?
- [ ] **Type Hints**: ¿Las funciones públicas cuentan con anotaciones de tipo completas (`list[str]`, `dict[str, Any]`, `np.ndarray`, etc.)?
