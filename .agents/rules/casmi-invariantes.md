# Regla Agéntica: Invariantes Críticos de Enveda CASMI 2026
**Ubicación**: `.agents/rules/casmi-invariantes.md`  
**Refuerzo Automático**: Hooks `H20`, `H21`, `H22`, `H23`, `H24`, `H27`.

Todo agente de IA o desarrollador humano que opere en este repositorio debe respetar de forma incondicional los siguientes invariantes del desafío:

1. **Métrica Oficial MRR@25 [H23]**:
   - Cada molécula (`molecule_id`) admite hasta 25 predicciones ordenadas de mayor a menor confianza.
   - Puntuación: Posición 1 = 1.0, 2 = 0.5, 25 = 0.04, fuera de 25 = 0.0. Solo la primera coincidencia suma.
2. **Canonicalización de Tautómeros [H20, H21]**:
   - RDKit está fijado estrictamente en `2026.03.3`.
   - Coincidencia sobre el primer bloque del InChIKey (**InChIKey14**) normalizado con `rdMolStandardize.TautomerEnumerator().Canonicalize()`.
3. **Validación Anti-Leakage [H22]**:
   - Particiones agrupadas por `molecule_id`, NUNCA por `spectrum_id`.
   - Agrupamiento estructural (Murcko Scaffolds / MCES) con subsets `Val-Clase1`, `Val-Clase2` y `Val-Clase3` evaluados sobre $\ge 3$ semillas deterministas.
4. **Formato de Entrega `submission.csv` [H24]**:
   - Separador de candidatos `;`. Columnas exactas `molecule_id,smiles`.
   - Máximo 25 SMILES por fila, sin NaN ni duplicados.
5. **Presupuesto de Cómputo de 9 Horas [H27]**:
   - El tiempo nominal total de inferencia no debe exceder 450 minutos para mantener un 20% de margen de seguridad frente al límite fatal de 540 minutos (9 horas).
