---
name: casmi-00-orchestrator
description: Mapa maestro del proyecto Enveda CASMI 2026 (Kaggle, identificación de moléculas a partir de espectros MS/MS, MRR@25). Úsala SIEMPRE que el usuario hable de la competencia CASMI/Enveda, pregunte por dónde empezar, el orden de trabajo, el cronograma, las 3 clases (fáciles/intermedias/fantasmas), los 3 pilares (A/B/C), prioridades, riesgos o el estado general del proyecto, o cuando una tarea toque varias fases a la vez. Enruta hacia las demás skills casmi-*.
---

# Orquestador CASMI 2026

## Objetivo del proyecto
Predecir, para cada `molecule_id` del test (~400 moléculas, ~1,500 espectros, timsTOF, 157–1,159 Da), una lista ordenada de hasta 25 SMILES separados por `;`. Métrica: **MRR@25** con coincidencia por **InChIKey14** tras canonicalizar tautómeros con RDKit.

## Fechas clave
- 14-sep-2026 inicio · **7-dic-2026** límite de inscripción y fusión de equipos · **14-dic-2026 11:59 PM UTC** cierre y entrega del notebook.
- Equipo máx. 5 personas; una cuenta por persona; colaboración privada solo dentro del equipo.
- Restricciones: notebook de Kaggle, ≤ 9 h, sin internet en la re-ejecución, datos externos solo si son públicos con licencia comercial válida.

## Las tres clases y su técnica
| Clase | Situación | Técnica | Skill |
|---|---|---|---|
| 1 Fáciles | Espectro en librerías públicas | Búsqueda por similitud espectral | 06 |
| 2 Intermedias | Estructura conocida, sin espectro público | Fingerprint predicho + matching por fórmula | 03, 05, 08 |
| 3 Fantasmas | Ausente de toda base pública | Generación de novo + verificación forward | 09, 10 |

La proporción real de clases en el test es **desconocida**. Por eso el arnés de validación (skill 04) mide cada clase por separado.

## Orden de trabajo recomendado
1. **01 + 04** primero: sin métrica fiel ni validación honesta, ninguna mejora es creíble.
2. **02, 03, 05**: datos, aductos/fórmula, universo de candidatos.
3. **06** Pilar A → **primer submit temprano** como línea base (y para validar el pipeline de entrega, skill 13).
4. **08** Pilar B, luego **09 + 10** Pilar C.
5. **07** fusión multi-espectro (mejora transversal).
6. **11** ensamble, **12** presupuesto en cascada, **13** empaquetado, **14** seguimiento.
7. Congelar el modelo unos días antes del 14-dic; reservar tiempo para pruebas de re-ejecución completa.

## Seis acciones clave (no negociables)
1. DreaMS como backbone del Pilar A, con fine-tuning ligero.
2. MIST como predictor de fingerprint central (alimenta B y C).
3. DiffMS (fórmula conocida) + contingencia tipo MARLIN (fórmula incierta) para Clase 3.
4. Cycle-consistency con CFM-ID/ICEBERG como señal de reranking en Clase 3.
5. Validación de 3 clases con split por MCES/scaffold, nunca aleatorio.
6. Ensamble LightGBM/XGBoost optimizado para MRR@25; nunca un solo score.

## Riesgos y mitigaciones
| Riesgo | Mitigación | Skill |
|---|---|---|
| Overfitting al leaderboard público (~400 mol., alta varianza) | ≥ 3 semillas de split; no afinar solo contra el público | 04, 14 |
| Fórmula mal estimada colapsa B/C | Contingencia tipo MARLIN + confianza de fórmula como feature | 03, 09 |
| Fingerprint imperfecto hunde candidatos correctos | Nunca rankear solo por Tanimoto | 08, 11 |
| Canonicalización local ≠ evaluador | RDKit idéntico; verificar InChIKey14 | 01 |
| Sesgo de dominio (productos naturales) | LOTUS (+ HMDB si la licencia lo permite) | 05 |

## Checklist maestro
- [ ] Preprocesamiento (02) · [ ] Split y 3 subsets, 3+ semillas (04) · [ ] RDKit fijo + InChIKey14 (01)
- [ ] Pilar A (06) · [ ] Pilar B (08) · [ ] Pilar C (09, 10) · [ ] Fusión multi-espectro (07)
- [ ] Ensamble para MRR@25 (11) · [ ] Presupuesto en cascada ≤ 9 h con margen (12)
- [ ] Pesos como datasets de Kaggle, sin internet (13) · [ ] Formato `submission.csv` (13) · [ ] Registro público vs. local (14)

## Cómo usar esta skill
Cuando el usuario pida algo concreto, identifica la fase en la tabla y lee la skill `casmi-NN-*` correspondiente antes de actuar. Si la petición cruza fases, resume el plan en pasos y menciona qué skill rige cada paso.
