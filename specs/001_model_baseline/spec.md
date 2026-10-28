# Especificación SDD: 001_model_baseline
## Ingesta, Filtrado de Espectros, Split Anti-Leakage de 3 Clases y Baseline Espectral

> **ID de Especificación**: `SPEC-001`  
> **Estado**: Aprobado para Ejecución  
> **Área**: Pipeline Base & Baseline Heurístico

---

## 1. Propósito y Alcance

### 1.1 Dentro de Alcance (In-Scope)
Esta especificación define los requisitos formales funcionales y no funcionales para:
- Ingestión inicial estructurada de `train.parquet` y `test.parquet`.
- Limpieza física, filtrado de ruido (<1% pico base), eliminación de overhang de precursor y deisotopado explícito.
- Normalización por tipo de aducto a masa neutra exacta.
- Partición anti-leakage por `molecule_id` y scaffold de Murcko, con validación estructural ECFP4/Tanimoto para `Val-Clase3` y tres semillas.
- Canonicalización estándar de tautómeros a InChIKey14 con RDKit `rdMolStandardize.TautomerEnumerator`.
- Implementación de la métrica oficial MRR@25.
- Motor de recuperación espectral baseline y formateador validado de `submission.csv`.

### 1.2 Fuera de Alcance (Out-of-Scope)
- **Modelos Generativos De Novo (Pilar C)**: El entrenamiento e inferencia de difusión discreta (DiffMS) y ciclo-consistencia (CFM-ID) se difieren formalmente al Sprint 3 (`SPEC-003`).
- **Conectividad a Red**: Queda estrictamente fuera de alcance cualquier llamada HTTP o acceso a internet en tiempo de inferencia; todo el pipeline opera 100% offline para paridad estricta con Kaggle.
- **Resolución Enantiomérica/Quiral**: La resolución de estereocentros queda fuera de alcance dado que el evaluador oficial canonicaliza formas tautoméricas y compara únicamente el bloque InChIKey14 sin penalización estereoquímica.

---

## 2. Requisitos Funcionales en Sintaxis EARS

### 2.1 Requisitos Ubicuos (Ubiquitous Requirements)
* **[REQ-UBI-01]**: El sistema debe normalizar las intensidades relativas de los picos de fragmentación de modo que el pico base sea exactamente 1.0.
* **[REQ-UBI-02]**: El sistema debe representar y evaluar las estructuras químicas ground-truth y predichas utilizando el primer bloque de 14 caracteres del InChIKey (InChIKey14), canonicalizado mediante `rdMolStandardize.TautomerEnumerator`.
* **[REQ-UBI-03]**: El sistema debe calcular el Mean Reciprocal Rank @ 25 (MRR@25) asignando $1/\text{rank}$ para coincidencias en posiciones 1 a 25, y 0.0 para posiciones $>25$ o no encontradas.
* **[REQ-UBI-04]**: El sistema debe fijar la semilla determinista global (seed=42) en Python, NumPy y PyTorch al inicio de cada pipeline.

### 2.2 Requisitos Basados en Eventos (Event-Driven Requirements)
* **[REQ-EVT-01]**: CUANDO el pipeline reciba un espectro con fragmentos que superen $\text{precursor\_mz} + 2.0\text{ Da}$, el preprocesador debe descartar dichos fragmentos de la lista `ms2_mzs`.
* **[REQ-EVT-02]**: CUANDO el pipeline procese un espectro de entrenamiento, el preprocesador debe descartar todos los picos con intensidad relativa inferior al 1% ($<0.01$) del pico base.
* **[REQ-EVT-03]**: CUANDO el generador de splits cree las particiones locales, el sistema debe agrupar los datos por `molecule_id`; `Val-Clase2` y `Val-Clase3` no deben compartir moléculas con train, mientras que `Val-Clase1` debe excluir su espectro de consulta y puede conservar los demás espectros de esa molécula en la biblioteca.
* **[REQ-EVT-04]**: CUANDO el split configure `Val-Clase3`, el sistema debe canonicalizar tautómeros con el enumerador compartido de `src/utils/metrics.py` antes de calcular scaffold Murcko y ECFP4; mantener los scaffolds de validación fuera de train, medir para cada molécula la distancia al vecino train más cercano y exigir una media estrictamente mayor que 0.60. Los scaffolds completos de vecinos con similitud de 0.40 o superior se excluirán de train.
* **[REQ-EVT-08]**: CUANDO el sistema lea los Parquet oficiales de Kaggle, debe mapear `inchikey14` a `molecule_id` y `normalized_smiles` a `label` en train, conservar los `molecule_id`/`spectrum_id` explícitos de test y asignar al train un `spectrum_id` estable basado en la fila cuando el origen no lo incluya. Para generar splits solo debe leer metadatos por lotes, sin retener arreglos de picos del dataset completo.
* **[REQ-EVT-09]**: CUANDO un consumidor lea un manifiesto compacto, debe poder reconstruir train y cada subset al recorrer el Parquet; el espectro de consulta de `Val-Clase1` debe excluirse de train.
* **[REQ-EVT-05]**: CUANDO el baseline reciba un espectro de query, el motor de inferencia debe recuperar hasta 25 candidatos únicos ordenados por similitud de precursor y fragmentos.
* **[REQ-EVT-06]**: CUANDO el preprocesador detecte patrones de picos isotópicos adyacentes (+1.0 Da, +2.0 Da), el sistema debe colapsar dichos picos a su especie monoisotópica principal antes del binning o cálculo de embeddings.
* **[REQ-EVT-07]**: CUANDO se procese el campo `adduct`, el sistema debe normalizar `precursor_mz` a masa neutra exacta del analito antes de realizar cualquier estimación de fórmula molecular.

### 2.3 Requisitos Basados en Estado (State-Driven Requirements)
* **[REQ-STA-01]**: MIENTRAS el sistema opere en modo de evaluación offline de Kaggle, el pipeline debe resolver las consultas utilizando únicamente artefactos de datos locales sin realizar conexiones de red.
* **[REQ-STA-02]**: MIENTRAS se procesen múltiples adquisiciones espectrales (`spectrum_id`) correspondientes a un mismo `molecule_id`, el sistema debe mantener trazabilidad íntegra del identificador de molécula.

### 2.4 Requisitos de Comportamiento No Deseado (Unwanted Behavior Requirements)
* **[REQ-ERR-01]**: SI un espectro contiene menos de 5 picos válidos tras la limpieza, ENTONCES el sistema debe emitir una advertencia estructurada y descartar el espectro del split de entrenamiento.
* **[REQ-ERR-02]**: SI un valor de SMILES en el conjunto de entrenamiento no puede ser parseado por RDKit, ENTONCES el sistema debe registrar el error en el log de auditoría y excluir la muestra de la indexación.
* **[REQ-ERR-03]**: SI una lista de predicciones generada para un `molecule_id` contiene más de 25 SMILES, ENTONCES el formateador de submisión debe truncar estrictamente la lista a los primeros 25 elementos.

### 2.5 Requisitos Opcionales (Optional Features)
* **[REQ-OPT-01]**: DONDE se disponga del tipo de aducto (`adduct`), el sistema debe calcular y registrar la masa neutra exacta del analito antes de estimar su fórmula elemental.
* **[REQ-OPT-02]**: DONDE se aplique transformación de intensidades, el sistema debe permitir configuración entre raíz cuadrada (`sqrt`) o escala logarítmica (`log1p`).

---

## 3. Criterios de Aceptación (DoD)
- Todas las funciones implementadas cuentan con tests unitarios con aserciones estrictas.
- La ejecución de `pytest tests/ -v` finaliza con código de salida 0.
- El archivo `submission.csv` generado cumple al 100% las especificaciones de Kaggle.
- La generación produce manifiestos JSON para las semillas 42, 1337 y 2026; cada uno registra la huella SHA-256 del train y ocupa menos de 25 MiB.
- Las pruebas de split comprueban disyunción, exclusión de consulta, reproducibilidad y distancia media Val-Clase3 a su vecino train más cercano mayor que 0.60.
