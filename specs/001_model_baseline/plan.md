# Plan de Implementación Técnica: 001_model_baseline
## Arquitectura del Modelo Baseline, Partición Anti-Leakage y Esquema de Evaluación

> **ID de Plan**: `PLAN-001`  
> **Feature**: Pipeline Base y Baseline de Recuperación Espectral  
> **Estado**: Listo para Construcción

---

## 1. Arquitectura del Flujo de Datos

```
[ train.parquet / test.parquet ]
               |
               v
   [ 1. Ingesta y Validación de Esquema (PyArrow/Polars) ]
               |
               v
   [ 2. Limpieza Espectral: Filtro <1% y Overhang precursor + 2 Da ]
               |
               v
   [ 3. Split Estructural por molecule_id + Murcko Scaffold (3 Semillas) ]
               |
      +--------+----------------------------+
      |                                     |
      v                                     v
 [ Train Set (~250k mol) ]         [ Validation Subsets (~25k mol) ]
      |                              |-- Val-Clase1 (Biblioteca)
      v                              |-- Val-Clase2 (Estructura conocida)
 [ 4. Indexador Baseline ]           +-- Val-Clase3 (Molécula Fantasma)
   (Mass-windowed matcher)                  |
      |                                     v
      +----------------------------> [ 5. Evaluador MRR@25 ]
                                            |
                                            v
                                 [ 6. submission.csv ]
```

---

## 2. Elección del Modelo Baseline
Para establecer el punto de partida sin incurrir en deuda técnica ni modelos opacos:
- **Modelo**: `BaselineSpectralMatcher` (retrieval heurístico basado en ventana de masa de precursor y conteo de fragmentos comunes).
- **Justificación**:
  - Corre en $< 1$ minuto sobre 50,000 espectros.
  - No requiere entrenamiento con GPU en esta etapa.
  - Sirve como prueba de humo (*smoke test*) para validar el arnés de evaluación local, el formato `submission.csv` y el cálculo de MRR@25 con InChIKey14.

---

## 3. Estrategia de Partición Anti-Leakage (3 Subsets de Validación)

El test oculto de Kaggle contiene ~400 moléculas distribuidas en 3 clases. Para evitar falsos positivos y sobreajuste:

1. **Aislamiento Estricto por `molecule_id`**: Nunca particionar por `spectrum_id`. Todos los espectros de una misma molécula quedan confinados a un único split.
2. **Generación de los 3 Subsets**:
   - **`Val-Clase1`**: Espectros de validación cuyos análogos de la misma molécula (o la misma molécula con distinto aducto) existen en la base de búsqueda.
   - **`Val-Clase2`**: Moléculas cuya estructura SMILES existe en el pool de candidatos, pero ningún espectro de la molécula está en el índice de búsqueda.
   - **`Val-Clase3`**: Moléculas estructuralmente distantes del conjunto de entrenamiento, seleccionadas mediante agrupamiento de scaffolds de Murcko o baja similitud Tanimoto ECFP4 ($< 0.40$).
3. **Repetición Multisemilla**: Generar splits con 3 semillas fijas (`seed=42`, `seed=1337`, `seed=2026`) para reportar media y desviación típica.

---

## 4. Estandarización Química y Métricas
- **Canonicalización InChIKey14**:
  Replicar de forma idéntica el evaluador de Kaggle utilizando `rdMolStandardize.TautomerEnumerator()` para eliminar discrepancias por formas tautoméricas o centros quirales.
- **Métrica Primaria**:
  $$MRR@25 = \frac{1}{|M|} \sum_{i=1}^{|M|} \frac{1}{\text{rank}_i}$$
  Calculada independientemente para `Val-Clase1`, `Val-Clase2` y `Val-Clase3`.

---

## 5. Gestión de Riesgos y Mitigación

| Riesgo Técnico | Severidad | Mitigación Arquitectónica |
|---|---|---|
| Fuga de datos entre espectros del mismo analito | Alta | Agrupación estricta por `molecule_id` en `splitter.py` con test de aserción de conjuntos disjuntos. |
| Incompatibilidad de versión de RDKit con Kaggle | Crítica | Anclar versión a `2026.03.3` (o la más reciente compatible) y encapsular `TautomerEnumerator` en `metrics.py`. |
| Desbordamiento de memoria RAM al cargar 2M espectros | Media | Carga diferida por batches o streaming con PyArrow IPC / Parquet chunking. |
| Error en formato de `submission.csv` | Crítica | Validador automatizado `validate_submission_csv()` ejecutado como test de integración previo al envío. |

