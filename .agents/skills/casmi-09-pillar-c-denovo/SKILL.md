---
name: casmi-09-pillar-c-denovo
description: Pilar C de CASMI 2026 (Clase 3, moléculas fantasma ausentes de toda base pública) — generación de novo con DiffMS (difusión discreta sobre grafos restringida por fórmula, encoder MIST), MSNovelist/SIRIUS 6 como segunda opinión y contingencia tipo MARLIN cuando la fórmula es incierta. Úsala siempre que se genere una estructura de novo, se afine DiffMS, se haga muestreo de candidatos generados, se hable de la fórmula incierta o de moléculas sin coincidencia en bases de datos.
---

# Pilar C — Generación de novo

## Arquitectura principal: DiffMS
Encoder-decoder restringido por fórmula. El **encoder** es un transformer tipo MIST que aprovecha conocimiento de dominio (fórmulas de picos, pérdidas neutras). El **decoder** es un modelo de **difusión discreta sobre grafos moleculares**, restringido por la composición atómica de la fórmula conocida. Su decodificador se preentrena con pares fingerprint–estructura, disponibles casi sin límite desde DSSTox, HMDB, COCONUT y MOSES (~2 M de compuestos), lo que compensa la escasez de pares espectro–estructura reales. Código abierto: `coleygroup/DiffMS`.

> **Antes de escribir código:** lee el README de DiffMS (entrada, pesos preentrenados disponibles, cómo muestrear N estructuras por espectro, tiempo por muestra, dependencias y modo offline). Verifica la **licencia** de los datos de preentrenamiento y de los pesos si vas a usar fuentes con restricciones comerciales (skill 05).

## Flujo
1. Entrada: top-k fórmulas con confianza (skill 03) + espectro(s) fusionados por molécula (skill 07).
2. **Muestreo:** genera N candidatos por (molécula, fórmula) (N de decenas a cientos; mide el tiempo/muestra antes de fijarlo, skill 12).
3. **Post-procesado:** valida SMILES con RDKit, **descarta los que no cumplen exactamente la fórmula**, deduplica por InChIKey14 (skill 01) y cuenta la **frecuencia de muestreo** de cada estructura (feature muy informativa).
4. Conserva log-verosimilitud o score del modelo si lo expone.
5. Pasa los candidatos a la verificación forward (skill 10) y al ensamble (skill 11).

## Complemento: MSNovelist (SIRIUS 6)
Úsalo como **segunda opinión** del ensamble. Su propia documentación advierte que la tasa de acierto en compuestos realmente novedosos es baja: trátalo como punto de partida, nunca como respuesta final. Comprueba que corre sin internet y su licencia antes de depender de él.

## Contingencia: fórmula incierta (tipo MARLIN)
Si la confianza de fórmula es baja (skill 03), el Pilar C no puede depender de una fórmula única. El masterplan prescribe un mecanismo tipo **MARLIN**: reutilizar un predictor de fingerprint y ajustarlo para la tarea generativa **sin depender de una fórmula de referencia garantizada**.

- Antes de implementarlo, **busca la publicación/código de MARLIN y confirma que está disponible, su licencia y que es viable offline.** Si no hay código usable en el tiempo disponible, **informa al usuario** en lugar de simular una implementación.
- **Plan de respaldo realista (disponible siempre):** ejecutar DiffMS sobre las top-k fórmulas plausibles (pesadas por su confianza), unir los candidatos y dejar que el ensamble pondere con `c_formula_conf` como feature. Es más barato que MARLIN y cubre parte del mismo riesgo.
- Activa la contingencia solo por debajo de un umbral de confianza calibrado en el arnés (skill 04).

## Salidas para el ensamble
Por candidato: `c_sample_freq`, `c_loglik`, `c_formula_conf`, `c_formula_rank`, `c_source` (diffms/msnovelist/respaldo), `c_matches_formula`.

## Verificación
MRR@25 en Val-Clase3 por semilla. Reporta también cuántas moléculas tienen la estructura verdadera **en algún lugar** de la lista generada (recall del generador) frente al MRR final: la diferencia indica cuánto puede ganar el reranking (skills 10 y 11).
