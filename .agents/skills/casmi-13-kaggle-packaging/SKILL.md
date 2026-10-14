---
name: casmi-13-kaggle-packaging
description: Empaquetado y entrega en Kaggle para CASMI 2026 — pesos y dependencias como datasets sin internet, instalación offline de paquetes, validación del formato exacto de submission.csv (hasta 25 SMILES por molecule_id separados por ';'), prueba de ejecución completa y checklist de entrega. Úsala siempre que se prepare el notebook final, se suban modelos o datos a Kaggle, falle algo sin internet, o se vaya a enviar una submission.
---

# Empaquetado y entrega

## Restricciones de la competencia
Notebooks de Kaggle obligatorios, ≤ 9 h, **internet desactivado** en la re-ejecución de evaluación, archivo de salida `submission.csv`, datos externos solo públicos con licencia comercial válida.

## Qué empaquetar como datasets
- Pesos: DreaMS (afinado), MIST, DiffMS afinado, SIRIUS/CSI:FingerID si se usa localmente, modelo del ensamble final (+ lista de features y su orden).
- Datos derivados: índice FAISS (o los embeddings para reconstruirlo), universo de candidatos (skill 05), splits no son necesarios en producción.
- **Paquetes Python:** descarga *wheels* localmente (`pip download -d wheels/ ...`), sube la carpeta como dataset e instala en el notebook con `pip install --no-index --find-links=/kaggle/input/<dataset>/wheels <paquete>`. Para RDKit fija la versión del masterplan (skill 01). Software no-Python (SIRIUS/Java, CFM-ID) requiere empaquetar el binario/contenedor y comprobar que se ejecuta en el entorno de Kaggle.
- **Límites de tamaño:** comprueba los límites actuales de datasets y notebooks de Kaggle en su documentación; si el universo de candidatos o el índice son enormes, redúcelos (filtro por masa, cuantización) en vez de descubrir el problema el último día.
- **Licencias:** registra en `LICENSES.md` la licencia de cada modelo y base de datos incluida (skill 05).

## Formato de `submission.csv`
- **Lee `sample_submission.csv` de la competencia** y copia exactamente los nombres de columnas y el orden de filas; no los adivines.
- Una fila por `molecule_id` del test; el campo de predicciones contiene **hasta 25 SMILES separados por `;`**, mejor candidato primero, sin duplicados (por InChIKey14) y sin SMILES inválidos.
- Ejecuta `scripts/validate_submission.py` sobre cada archivo antes de enviarlo.

## Notebook final: orden recomendado
1. Chequeos de entorno (versión RDKit, GPU, rutas de datasets) y arranque del reloj de guardia (skill 12).
2. Carga y preprocesado (02) → fórmula (03) → fusión (07).
3. Pilar A (06) → primera escritura de `submission.csv`.
4. Pilar B (08) → actualización.
5. Pilar C + verificación (09, 10) solo para moléculas no resueltas.
6. Ensamble (11) → `dedupe_topk` → escritura final y validación.

## Checklist previo a cada envío
- [ ] Corre completo con internet desactivado y dentro del tiempo (skill 12).
- [ ] No hay rutas absolutas locales ni descargas en tiempo de ejecución.
- [ ] `validate_submission.py` sin errores.
- [ ] Versión de RDKit idéntica a la de validación.
- [ ] Resultados registrados en la skill 14.
- [ ] Notebook final seleccionado para la evaluación antes del cierre (14-dic, 11:59 PM UTC); no dejes la selección para el último minuto.

