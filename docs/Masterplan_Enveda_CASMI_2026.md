# Masterplan Técnico: Enveda CASMI 2026 — Molecule ID From Mass Spectra

---

## 1. Descripción del Desafío

El desafío **Enveda CASMI 2026 - Molecule ID From Mass Spectra** de Kaggle, respaldado por *Enveda Biosciences*, retoma el certamen *Critical Assessment of Small Molecule Identification* (CASMI). El objetivo es **predecir estructuras químicas bidimensionales (en formato SMILES) de moléculas pequeñas a partir de espectros de masas en tándem (LC-MS/MS)**, especialmente de compuestos extraídos de fuentes biológicas complejas (plantas y microbios).

### 1.1 Cronograma
* **14 de septiembre, 2026:** inicio de la competencia.
* **7 de diciembre, 2026:** límite de inscripción y de formación/fusión de equipos.
* **14 de diciembre, 2026:** cierre definitivo y entrega final de *Notebooks* (11:59 PM UTC).

### 1.2 Premios
* Bolsa total: **$50,000 USD** — 1.° $16,000 · 2.° $12,000 · 3.° $9,000 · 4.° $7,000 · 5.° $6,000, más puntos y medallas de Kaggle.

### 1.3 Reglas de Equipo
* Máximo **5 personas** por equipo (se permite competir individualmente).
* Una sola cuenta por participante; nadie puede pertenecer a más de un equipo en paralelo.
* Fusiones permitidas antes del 7 de diciembre de 2026, sin superar el tope de 5 integrantes.
* Colaboración privada solo entre miembros del equipo oficial; cualquier aporte comunitario debe publicarse en foros o notebooks públicos.

---

## 2. Arquitectura de los Datos

* **`train.parquet`:** ~2 millones de espectros MS/MS, ~275,000 estructuras únicas (GNPS, MassBank, MoNA, RIKEN + macro-librería Enveda-180).
* **`test.parquet`:** ~1,500 espectros correspondientes a ~400 moléculas ocultas, medidas en Bruker timsTOF (masas de 157 a 1,159 Da).

### 2.1 Las Tres Clases del Test — y su Técnica Dominante
| Clase | Descripción | Técnica dominante |
|---|---|---|
| **1 — Fáciles** | Espectro presente en librerías públicas | Búsqueda directa por similitud espectral (Pilar A) |
| **2 — Intermedias** | Estructura conocida (PubChem/COCONUT), sin espectro público | Fingerprint predicho + matching por fórmula (Pilar B) |
| **3 — Fantasmas** | Ausente de toda base de datos pública | Generación *de novo* + verificación forward (Pilar C) |

> La proporción real entre estas tres clases en el test oculto es desconocida — la estrategia de validación (Sección 5) está diseñada precisamente para medir el rendimiento por separado en cada una y así saber dónde invertir el tiempo de desarrollo.

### 2.2 Campos Principales del Dataset
* `molecule_id`: identificador anónimo de la sustancia.
* `spectrum_id`: identificador de cada adquisición espectral (una molécula puede tener varias, a distintas energías de colisión/aductos).
* `ms2_mzs`: arreglo de masas fragmentadas ($m/z$).
* `ms2_normalized_intensities`: intensidades relativas (pico base = 1.0).
* `precursor_mz`: masa-carga del ion intacto antes de fragmentar.
* `adduct`: tipo de ionización (`[M+H]+`, `[M-H]-`, `[M+NH4]+`, `[M+2H]2+`, etc.).
* `collision_energy_ev`: energía de colisión aplicada.
* `label`: SMILES canónico (solo en train).

---

## 3. Métrica de Evaluación y Criterio de Coincidencia

* **Métrica:** Mean Reciprocal Rank @ 25 (**MRR@25**):
  $$MRR@25 = \frac{1}{\vert{}M\vert{}} \sum_{i=1}^{\vert{}M\vert{}} \frac{1}{\text{rank}_i}$$
* **Formato de envío:** por cada `molecule_id`, una lista ordenada de hasta **25 candidatos SMILES** separados por `;`, con la mejor suposición primero.
  * Posición 1 = `1.0`; posición 2 = `0.5`; posición 25 = `0.04`; fuera del top 25 = `0`. Solo cuenta la primera coincidencia correcta.
* **Criterio de coincidencia:** predicción y respuesta real se canonicalizan por tautómeros con **RDKit `2026.03.3`** y se reducen al primer bloque del InChIKey (**InChIKey14**) — no se penalizan errores de estereocentros ni de forma tautomérica.

> ⚠️ **Punto crítico de implementación:** el pipeline de validación local debe replicar exactamente esta canonicalización (misma versión de RDKit, mismo `rdMolStandardize.TautomerEnumerator`). Un desajuste aquí hace que el MRR@25 local deje de correlacionar con el del leaderboard.

---

## 4. Restricciones Técnicas del Entorno (Code Competition)

* **Plataforma:** Notebooks de Kaggle obligatorios.
* **Tiempo límite:** máximo **9 horas** de ejecución (CPU o GPU).
* **Acceso a internet:** desactivado durante la re-ejecución de evaluación — todos los pesos y modelos deben empaquetarse previamente como datasets de Kaggle.
* **Datos externos:** permitidos si son de acceso público y con licencia comercial válida.
* **Archivo de salida:** obligatoriamente `submission.csv`.
* **Implicación de presupuesto:** con ~400 moléculas de test y 9h de límite, hay que presupuestar explícitamente el tiempo por pilar (Sección 8.3) — una arquitectura en cascada es obligatoria, no opcional.

---

## 5. Preprocesamiento de Espectros y Validación Local

### 5.1 Limpieza y Normalización Base
* Umbral de intensidad relativa: eliminar picos por debajo del 1-2% del pico base.
* Filtro de precursor ($m/z$): descartar fragmentos que superen la masa del precursor (+~2 Da de tolerancia isotópica).
* Control de densidad: descartar espectros con <5 picos; en espectros densos, conservar los *Top-N* picos más informativos o filtrar por ventanas de masa.
* Transformación de intensidades (raíz cuadrada o logaritmo) para evitar que picos dominantes distorsionen el entrenamiento.

### 5.2 Pasos Avanzados Obligatorios
* **Deisotopado explícito:** colapsar picos isotópicos (+1, +2 Da) a su especie monoisotópica antes de cualquier *binning*/*embedding*.
* **Normalización por tipo de aducto:** convertir `precursor_mz` a masa neutra exacta según el aducto (`[M+H]+`, `[M+Na]+`, `[M+2H]2+`, pérdidas de agua, etc.) **antes** de estimar la fórmula molecular — fuente común de bugs silenciosos si se omite.
* **Similitud por entropía espectral** (Li et al., 2021) como complemento al coseno para la búsqueda directa — más robusta al ruido instrumental de un timsTOF.
* **Deduplicación** de espectros casi-idénticos para no sesgar el entrenamiento hacia moléculas sobre-representadas.

### 5.3 Estrategia de Validación Local (Anti-Overfitting)

**Reglas de split:**
* Split por `molecule_id`, nunca por `spectrum_id` (evita que dos espectros de la misma molécula caigan uno en train y otro en validación).
* Split por agrupamiento estructural — idealmente por **distancia de Máximo Subgrafo Común de Aristas (MCES)**, o como alternativa por scaffold de Murcko / clustering de fingerprints ECFP4 (Tanimoto) — para simular realmente la Clase 3, donde un split aleatorio sobreestima el rendimiento al dejar "primos estructurales" en train.

**Tres subsets de validación simulados**, replicando las condiciones del test oculto:

| Subset | Espectro en índice de búsqueda | SMILES en base de candidatos | Simula |
|---|---|---|---|
| Val-Clase1 | Sí | Sí | Búsqueda directa en librería |
| Val-Clase2 | No | Sí | Estructura conocida sin espectro público |
| Val-Clase3 | No | No | Molécula "fantasma", de novo |

* Reportar MRR@25 por separado en cada subset, con al menos 3 semillas de split distintas (el test real es pequeño, ~400 moléculas → alta varianza muestral).
* El score final del leaderboard será aproximadamente un promedio ponderado por la proporción real de cada clase — usar estos tres números para priorizar dónde mejorar.

---

## 6. Pipeline de Modelado — Tres Pilares

### 6.1 Pilar A — Motor de Recuperación (Clase 1)
* **Embeddings espectrales:** usar **DreaMS** como *backbone* preentrenado — modelo fundacional autosupervisado entrenado sobre más de 200 millones de espectros MS/MS, con pesos y código abiertos, que generaliza entre instrumentos y condiciones experimentales. Aplicar *fine-tuning* ligero sobre el train de la competencia en vez de entrenar un transformer espectral desde cero (más eficiente dado el límite de 9 horas).
* **Búsqueda indexada:** FAISS con índice **IVF-PQ** (no flat) dado el volumen de ~2M vectores del train.
* **Señal complementaria:** combinar coseno de embeddings DreaMS con *spectral entropy similarity* clásica — ambas se incorporan como features del ensamble final (Sección 6.4), no se sustituyen entre sí.

### 6.2 Pilar B — Fingerprint + Matching por Fórmula (Clase 2)
Flujo completo:
1. **Estimación de fórmula molecular exacta** a partir de la masa neutra (ya corregida por aducto) y el patrón isotópico.
2. **Filtrado por restricciones químicas:** valencia y DBE (índice de dobles enlaces y anillos) para descartar candidatos físicamente imposibles.
3. **Predicción de fingerprint molecular desde el espectro:** usar **MIST** como predictor principal — es hoy el predictor neuronal de fingerprint más fuerte y abierto disponible, y el mismo componente que alimenta el modelo generativo del Pilar C, por lo que mejorar MIST beneficia a ambos pilares simultáneamente. Usar **SIRIUS 6 / CSI:FingerID** (con su score de confianza COSMIC) como señal complementaria del ensamble, no como sustituto.
4. **Universo de candidatos:** generar el conjunto que cumpla exactamente la fórmula, consultando PubChem, COCONUT, LOTUS y HMDB (Sección 6.4).
5. **Ranking por similitud de Tanimoto** entre el fingerprint predicho y el fingerprint real de cada candidato.

> El ranking por Tanimoto es sensible a errores del fingerprint predicho. Por eso nunca debe usarse como único criterio: se combina siempre con la señal espectral directa del Pilar A y el error de masa dentro del ensamble final (Sección 7).

### 6.3 Pilar C — Generación *De Novo* (Clase 3)
* **Arquitectura principal: DiffMS** — encoder-decoder restringido por fórmula, donde el encoder es un transformer (MIST) que modela conocimiento de dominio (fórmulas de picos, pérdidas neutras) y el decoder es un **modelo de difusión discreta sobre grafos moleculares, restringido por la composición atómica de la fórmula química conocida**. Su decodificador se preentrena con pares fingerprint-estructura (disponibles casi ilimitadamente desde DSSTox, HMDB, COCONUT y MOSES, ~2M compuestos), compensando la escasez de pares espectro-estructura reales. Código abierto disponible (`coleygroup/DiffMS`).
* **Complemento:** **MSNovelist** (integrado en SIRIUS 6) como segunda opinión de ensamble; su propia documentación advierte que la tasa de acierto en compuestos verdaderamente novedosos es baja, así que sus resultados deben tratarse como punto de partida, no como respuesta final.
* **Salvaguarda para fórmula mal estimada:** dado que el Pilar B/C depende de una fórmula correcta, incorporar un mecanismo tipo **MARLIN** (reutiliza un predictor de fingerprint pero genera la estructura ajustando ese predictor para la tarea generativa, sin depender de una fórmula de referencia garantizada) como plan de contingencia cuando la confianza en la fórmula estimada sea baja.
* **Verificación por cycle-consistency:** re-simular el espectro teórico de cada candidato de novo con un modelo *forward* (**CFM-ID** o **ICEBERG**) y compararlo contra el espectro real observado. Esta señal de consistencia reordena los candidatos generados y es la técnica que distingue a los mejores resultados en la categoría de novo.

### 6.4 Ampliación del Universo de Candidatos y Fusión Multi-Espectro
* **Bases de candidatos:** además de PubChem y COCONUT, agregar **LOTUS** (productos naturales, curada por taxonomía planta/organismo) y **HMDB** (metaboloma humano) — dado el origen biológico del dataset de Enveda (plantas/microbios), es probable que moléculas "fantasma" tengan parientes cercanos en estas bases especializadas aunque no figuren en PubChem.
* **Fusión multi-espectro:** promediar/agregar (ponderado por calidad/número de picos) los embeddings DreaMS de todos los `spectrum_id` de un mismo `molecule_id` de test antes del retrieval final del Pilar A — reduce varianza y ruido instrumental.
* **Consistencia entre energías de colisión:** picos que persisten a través de múltiples energías de colisión suelen corresponder a fragmentos estructuralmente robustos — señal adicional para el filtrado de fórmula del Pilar B.

---

## 7. Re-ranking Final y Ensamble

Entrenar un modelo de *gradient boosting* (**LightGBM** o **XGBoost**) que combine, para cada candidato SMILES generado por cualquiera de los tres pilares, las siguientes señales:
* Similitud espectral (coseno DreaMS + entropía espectral) del Pilar A.
* Tanimoto entre fingerprint MIST predicho y fingerprint real del candidato (Pilar B).
* Score de confianza COSMIC de SIRIUS/CSI:FingerID (señal independiente de MIST).
* Error de masa respecto a la fórmula estimada y score DBE.
* Log-verosimilitud del modelo generativo (Pilar C), si aplica.
* Score de *cycle-consistency* (similitud entre espectro teórico re-simulado y espectro real observado).

**Objetivo de entrenamiento:** optimizar directamente **MRR@25** sobre los tres subsets de validación (Sección 5.3) — no accuracy ni AUC genéricos, que no capturan la naturaleza de "ranking con recompensa decreciente" de la métrica real.

### Tabla de Riesgos y Mitigaciones
| Riesgo | Mitigación |
|---|---|
| Overfitting al leaderboard público (~400 moléculas, alta varianza) | Validar con 3+ semillas de split; no ajustar hiperparámetros solo contra el público |
| Fórmula molecular mal estimada colapsa el Pilar B/C | Salvaguarda tipo MARLIN + score de confianza de la fórmula como feature del ensamble |
| Fingerprint predicho imperfecto hunde candidatos correctos | Nunca rankear solo por Tanimoto; combinar siempre con señal espectral directa |
| Desajuste entre canonicalización local y la del evaluador | Fijar RDKit `2026.03.3` idéntico en desarrollo; verificar InChIKey14 en cada test local |
| Sesgo de dominio (Enveda = productos naturales) mal cubierto por PubChem | LOTUS + HMDB en el universo de candidatos |

### 8.3 Presupuesto de Cómputo (Cascada dentro de 9 horas)
Arquitectura en cascada: **Clase 1 (rápido, retrieval) → Clase 2 (medio, fingerprint + matching) → Clase 3 (costoso, generación + verificación forward)**, aplicando el Pilar C solo a las moléculas que A y B no resuelven con alta confianza. Presupuestar explícitamente minutos por molécula en cada pilar antes de la ejecución final, dejando margen de seguridad (~15-20%) para variabilidad del hardware de Kaggle.

---

## 8. Empaquetado y Entrega

* Empaquetar todos los pesos (DreaMS, MIST/DiffMS *fine-tuneado*, SIRIUS/CSI:FingerID si se usa localmente, modelo de ensamble final) como datasets de Kaggle, sin dependencia de internet en la re-ejecución de evaluación.
* Verificar que el notebook completo (los tres pilares + ensamble) corre dentro de las 9 horas con el presupuesto en cascada de la Sección 8.3.
* Verificar el formato exacto de `submission.csv`: hasta 25 SMILES por `molecule_id`, separados por `;`, mejor candidato primero.
* Registrar en cada envío el MRR@25 público vs. el MRR@25 local por clase, para detectar si el modelo sobreajusta al leaderboard público o si la proporción real de clases difiere de lo asumido en la validación.

---

## 9. Caja de Herramientas de Python

| Necesidad | Herramienta |
|---|---|
| Limpieza de espectros, similitud coseno/entropía | `matchms` |
| Fingerprints, canonicalización, tautómeros | `rdkit` + `rdMolStandardize` |
| Estandarización de estructuras | `molvs` |
| Embeddings espectrales fundacionales | **DreaMS** (pesos abiertos) |
| Predicción de fingerprint espectro→estructura | **MIST**; complementario: SIRIUS 6 / CSI:FingerID (score COSMIC) |
| Generación de novo restringida por fórmula | **DiffMS** (`coleygroup/DiffMS`); alternativa: MSNovelist (SIRIUS 6) |
| Salvaguarda sin fórmula confiable | Enfoque tipo **MARLIN** |
| Modelo forward (espectro teórico desde SMILES) | `CFM-ID` o `ICEBERG` |
| Búsqueda de similitud a escala | `FAISS` (IVF-PQ) |
| Bases de candidatos por fórmula | PubChem, COCONUT, LOTUS, HMDB |
| Boosting para el re-ranker final | `LightGBM` / `XGBoost` |
| Metodología de split anti-leakage | Clustering por MCES, o scaffold/Tanimoto ECFP4 |

---

## 10. Estrategia Ganadora — Las 6 Acciones Clave

1. **DreaMS como backbone obligatorio del Pilar A**, con *fine-tuning* ligero — es el modelo fundacional abierto de referencia; entrenar embeddings desde cero con 9h de presupuesto es una desventaja innecesaria.
2. **MIST como predictor de fingerprint central**, porque alimenta simultáneamente el Pilar B (matching) y el Pilar C (generación vía DiffMS) — es la pieza de mayor apalancamiento de todo el pipeline.
3. **DiffMS + salvaguarda tipo MARLIN para la Clase 3**, cubriendo tanto el caso "fórmula correcta conocida" (DiffMS) como el caso "fórmula incierta" (MARLIN).
4. **Verificación por cycle-consistency (CFM-ID/ICEBERG)** como señal de reranking en Clase 3 — costosa computacionalmente, por eso es la mayor ventaja diferencial.
5. **Arnés de validación de 3 clases con split por MCES/scaffold**, nunca aleatorio — sin esto, cualquier mejora percibida puede ser ruido.
6. **Ensamble final (LightGBM) que combina todas las señales de la Sección 7**, optimizado directamente para MRR@25 — nunca depender de un solo score (ni Tanimoto solo, ni coseno solo) como criterio de ranking final.

---

## 11. Checklist de Ejecución

- [ ] Preprocesamiento: deisotopado, normalización por aducto, filtro de precursor, transformación de intensidades.
- [ ] Split de validación por `molecule_id` + clustering MCES/scaffold, con los 3 subsets Val-Clase1/2/3, 3+ semillas.
- [ ] RDKit `2026.03.3` replicado exactamente en local; verificación de InChIKey14.
- [ ] Pilar A: DreaMS (fine-tuned) + FAISS IVF-PQ + coseno/entropía espectral.
- [ ] Pilar B: fórmula → MIST (fingerprint) → matching Tanimoto vs. PubChem/COCONUT/LOTUS/HMDB → señal complementaria SIRIUS/CSI:FingerID.
- [ ] Pilar C: DiffMS (fórmula conocida) + MARLIN (fórmula incierta) + verificación cycle-consistency (CFM-ID/ICEBERG).
- [ ] Fusión multi-espectro por `molecule_id` antes del retrieval final.
- [ ] Ensamble LightGBM/XGBoost con todas las señales, optimizado para MRR@25 sobre los 3 subsets.
- [ ] Presupuesto de tiempo validado en cascada (Clase 1 → 2 → 3) dentro de 9h, con margen de seguridad.
- [ ] Todos los pesos empaquetados como datasets de Kaggle (sin dependencia de internet).
- [ ] Formato final de `submission.csv` verificado.
- [ ] Registro de MRR@25 público vs. local por clase en cada envío.
