---
name: casmi-03-adduct-formula
description: Conversión de precursor_mz a masa neutra exacta según el aducto ([M+H]+, [M-H]-, [M+Na]+, [M+NH4]+, [M+2H]2+, pérdidas de agua) y estimación de fórmula molecular con filtros de valencia y DBE para CASMI 2026. Úsala siempre que se calcule la masa neutra, se estime o filtre una fórmula, se consulte un candidato por fórmula, se evalúe la confianza de la fórmula o se sospeche un bug silencioso de aducto. Es prerrequisito de los pilares B y C.
---

# Aductos y fórmula molecular

## Regla de oro
Convierte `precursor_mz` a **masa neutra M** según el aducto **antes** de estimar la fórmula. Omitirlo (o asumir `[M+H]+` para todo) es un bug silencioso muy común que corrompe los pilares B y C sin lanzar errores.

## Conversión m/z → M
`scripts/adducts.py` contiene la tabla de aductos con masas de iones (no de átomos neutros; se resta la masa del electrón) y la función `neutral_mass(mz, adduct)`. Ejemplos de fórmulas: `[M+H]+: M = mz − 1.007276` · `[M−H]−: M = mz + 1.007276` · `[M+2H]2+: M = 2·mz − 2·1.007276` · `[M+H−H2O]+: M = mz − 1.007276 + 18.010565`.
- Aducto desconocido o mal escrito → no adivines: marca el espectro con `adduct_ok = False` y usa una estrategia de respaldo (probar aductos plausibles y quedarse con los que den fórmulas consistentes).
- Con varios espectros de la misma molécula en aductos distintos (skill 07), las masas neutras deben coincidir; la **discrepancia entre aductos** es una señal de calidad.

## Estimación de fórmula
1. Enumera composiciones (`decompose` en el script) dentro de una tolerancia en ppm (empieza en ~5 ppm para timsTOF; ajusta con datos) y límites por elemento. Por defecto CHNOPS; añade F/Cl/Br/I solo cuando haya evidencia (patrón isotópico, pérdidas neutras) o como pasada secundaria, porque ampliar el espacio multiplica los falsos positivos.
2. **Filtros químicos:** DBE ≥ 0 y entero para una molécula neutra de capa cerrada (esto implementa también la regla del nitrógeno), valencia plausible, razones H/C razonables.
3. **Patrón isotópico:** puntúa cada fórmula comparando la distribución isotópica teórica con la observada en MS1 si está disponible; si el dataset solo trae MS2, usa los fragmentos (cada pico debe ser una subfórmula de la fórmula del precursor) como evidencia, apoyándote en las pérdidas neutras.
4. **Salida:** lista ordenada de fórmulas con `ppm_error`, `dbe`, `isotope_score`, `fragment_support` y una **confianza de fórmula** normalizada. Esa confianza es una feature del ensamble (skill 11) y decide si se activa la contingencia tipo MARLIN (skill 09).
5. Si hay varias fórmulas plausibles, **no te quedes solo con la primera**: pasa las top-k fórmulas a los pilares B/C y deja que el ensamble pondere.

## Verificación
- Test unitario con 10–20 moléculas de train: la fórmula verdadera (calculada desde el SMILES con RDKit) debe estar en el top-k de fórmulas estimadas; reporta el *recall@k de fórmula* por aducto. Si es bajo, es un problema de aductos/tolerancia, no del modelo.
- Compara con SIRIUS (decomposición de fórmula) como referencia cruzada si está disponible.
