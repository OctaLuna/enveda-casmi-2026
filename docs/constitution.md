# Constitución Técnica del Proyecto CASMI 2026
## Los 6 Principios Innegociables de Ingeniería y Gobernanza

> **Estado**: Vigente y Vinculante para todos los Desarrolladores (Dev 1, Dev 2, Dev 3) y Agentes de IA.  
> **Alcance**: Repositorio del Desafío Kaggle *Enveda CASMI 2026 — Molecule ID From Mass Spectra*.

---

### Principio 1: Separación Estricta de Responsabilidades de Pipeline
* **Mandato**: Queda terminantemente prohibido mezclar en un mismo script o módulo la limpieza/preprocesamiento de espectros, el entrenamiento/indexado de modelos y la evaluación/inferencia.
* **Estructura Requerida**:
  * `src/data/`: Exclusivo para parsing, filtros de picos, deisotopado, corrección de aductos y generación de splits estructurales.
  * `src/models/`: Exclusivo para arquitecturas, entrenamiento, generación de embeddings (DreaMS/MIST/DiffMS) e indexación FAISS.
  * `src/api/` o `src/inference/`: Exclusivo para la ejecución de la cascada de inferencia y formateo de `submission.csv`.
  * `src/utils/`: Funciones puras de cálculo de métricas (MRR@25), estandarización InChIKey14 y logging.
* **Consecuencia de Incumplimiento**: Los PRs que contengan scripts monolíticos "todo-en-uno" serán rechazados automáticamente.

---

### Principio 2: Control de Versiones de Modelos y Experimentos (Inmutabilidad de Artefactos)
* **Mandato**: Ningún artefacto de pesos (`.pt`, `.onnx`), índice FAISS (`.index`) o checkpoint de modelo podrá ser sobrescrito en disco.
* **Políticas**:
  * Todo modelo entrenado o exportado debe contener un identificador único con timestamp semántico y hash de configuración (ej. `models/checkpoints/mist_fingerprint_v0.1.0_20261015_e12.pt`).
  * Los parámetros, métricas por subset (Val-Clase1, Val-Clase2, Val-Clase3) y metadatos deben registrarse rigurosamente en MLflow con sus tags de commit de Git correspondientes.
  * Queda prohibido trackear archivos binarios mayores a 50MB en el repositorio Git; deberán gestionarse como Kaggle Datasets o almacenamiento remoto versionado.

---

### Principio 3: Política Estricta de Testing (TDD y Cobertura de Pipeline)
* **Mandato**: No se considerará completada ninguna tarea ni se aceptará ningún Pull Request si no cuenta con pruebas unitarias asociadas y passing en `tests/`.
* **Políticas**:
  * Las funciones de preprocesamiento de espectros (deisotopado, normalización de masa neutra según aducto, cálculo de entropía espectral) deben contar con tests que verifiquen casos de borde conocidos (ej. aductos multivariantes, espectros vacíos o ruidosos).
  * La función de cálculo de métrica local `calculate_mrr_at_25` y canonicalización tautomérica `rdMolStandardize` con InChIKey14 debe contar con tests de regresión con datos de juguete antes de ser utilizada en benchmarks.
  * La suite de tests debe ejecutarse en menos de 60 segundos para tests unitarios locales.

---

### Principio 4: Reproducibilidad Garantizada y Gestión Estricta de Semillas
* **Mandato**: Todo cálculo probabilístico, inicialización de tensores o particionamiento de datos debe producir resultados exactamente idénticos en distintas ejecuciones.
* **Políticas**:
  * Es obligatorio invocar `src.utils.reproducibility.set_seed(seed)` al inicio de todo pipeline o script de entrenamiento.
  * Prohibido realizar splits aleatorios no estratificados. Los splits de validación deben basarse en agrupación por `molecule_id` y clustering estructural (distancia MCES o scaffold Murcko/Tanimoto ECFP4) fijando la semilla aleatoria.
  * Las dependencias deben estar estrictamente fijadas en `requirements.txt` asegurando paridad con el entorno de Kaggle Notebooks (especialmente RDKit `2026.03.3`).

---

### Principio 5: Spec-Driven Development (SDD) Sin "Vibe Coding"
* **Mandato**: Ningún desarrollador ni agente de IA escribirá código de producción en `src/` basado en intuición o improvisación ("vibe coding").
* **Flujo Obligatorio**:
  1. **Especificación (`specs/<feature>/spec.md`)**: Requisitos funcionales formales redactados en sintaxis EARS (*Easy Approach to Requirements Syntax*).
  2. **Plan Técnico (`specs/<feature>/plan.md`)**: Diseño detallado de arquitectura, flujos de datos, validación y gestión de riesgos.
  3. **Tareas Atómicas (`specs/<feature>/tasks.md`)**: Lista de tareas atómicas (20-30 minutos) con dependencias explícitas y asignación a Dev 1, Dev 2 o Dev 3.
  4. **Implementación Test-First**: Redacción de la prueba en `tests/` y desarrollo en `src/`.
* **Consecuencia**: El agente rechazará cualquier instrucción que intente modificar `src/` sin referencia a una tarea activa en `specs/`.

---

### Principio 6: Colaboración Git Sin Conflictos para 3 Desarrolladores
* **Mandato**: La arquitectura de código y la división del trabajo deben garantizar un flujo de integración continua sin bloqueos ni merge conflicts destructivos.
* **Distribución de Dominios**:
  * **Dev 1 (Data & Validation Core)**: `src/data/`, `src/utils/metrics.py`, `src/utils/reproducibility.py`, tests de datos y validación de splits.
  * **Dev 2 (Retrieval & Fingerprints - Pilares A y B)**: `src/models/retrieval/` (DreaMS, FAISS), `src/models/fingerprints/` (MIST, SIRIUS/COSMIC), matching de candidatos en bases externas.
  * **Dev 3 (Generative De Novo & Ensembling - Pilar C y Submission)**: `src/models/generative/` (DiffMS, MARLIN), `src/models/forward/` (CFM-ID/ICEBERG), `src/models/ensemble/` (LightGBM/XGBoost) y `src/api/submission.py`.
* **Reglas de Interfaz**:
  * La comunicación entre módulos se realiza exclusivamente a través de interfaces tipadas (dataclasses/Pydantic) definidas previamente en `specs/`.
  * Trabajo en ramas feature (`feature/<sprint>-<dev>-<nombre>`), PRs con revisión de código obligatoria y prohibición de commits directos sobre la rama `main`.
