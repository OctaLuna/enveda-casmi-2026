---
name: casmi-06-pillar-a-retrieval
description: Pilar A de CASMI 2026 (Clase 1, espectros presentes en librerías públicas) — embeddings DreaMS con fine-tuning ligero, índice FAISS IVF-PQ sobre ~2M vectores, búsqueda por similitud y combinación con coseno y spectral entropy similarity. Úsala siempre que se haga búsqueda/retrieval espectral, se calculen embeddings DreaMS, se construya o ajuste FAISS, se hable de similitud por entropía o de la línea base de Clase 1.
---

# Pilar A — Motor de recuperación

## Decisión de diseño
Usa **DreaMS** como backbone preentrenado (modelo fundacional autosupervisado, > 200 M de espectros MS/MS, pesos y código abiertos, generaliza entre instrumentos). **No entrenes un transformer espectral desde cero:** con un límite de 9 h es una desventaja innecesaria. Aplica un fine-tuning ligero sobre el train de la competencia.

> **Antes de escribir código:** revisa el README del repositorio de DreaMS (pluskal-lab/DreaMS) para el nombre exacto de la API de embeddings, el formato de entrada, la dimensión del embedding y cómo cargar pesos offline. No inventes llamadas.

## Flujo
1. **Preprocesa** con la skill 02 (el formato de entrada de DreaMS puede exigir su propio preprocesado; respétalo y documenta cualquier diferencia).
2. **Embeddings** de todo el train y del test. Normaliza L2 para usar producto interno como coseno. Guarda en `float16/float32` en un `.npy` memmap por lotes.
3. **Índice FAISS IVF-PQ** (no flat; ~2 M vectores):
   - Entrena el cuantizador con una muestra (≥ 30–50× `nlist`).
   - `nlist` de orden de miles (p. ej. 4096–8192 para 2 M); `m` (subvectores de PQ) debe **dividir la dimensión** del embedding; `nbits=8`.
   - Ajusta `nprobe` con el arnés (compromiso recall/latencia). Mide el recall frente a una búsqueda exacta sobre una submuestra.
   - `faiss-cpu` es suficiente si el presupuesto lo permite; confirma la disponibilidad de la versión GPU en Kaggle antes de depender de ella.
4. **Recuperación en dos etapas:** FAISS devuelve top-K (p. ej. 200–500) espectros; luego **re-puntúa** cada par con *spectral entropy similarity* sobre los picos reales.
5. **Agrega por molécula:** del top-K de espectros, agrupa por InChIKey14 de `label` y conserva el **mejor** score (y el número de espectros que coinciden) por molécula; devuelve las top-25 estructuras únicas.
6. **Filtro opcional por masa:** exige que la masa neutra (skill 03) de la estructura candidata coincida con la del query dentro de la tolerancia; descarta o penaliza el resto. Verifica con el arnés si ayuda.

## Spectral entropy similarity (Li et al., 2021)
Complemento al coseno, más robusto al ruido de un timsTOF. Procedimiento: fusionar picos de los dos espectros con tolerancia de m/z, normalizar cada intensidad a suma 1 (con la re-ponderación de intensidades por entropía que describe el artículo), y calcular `sim = 1 − (2·S_AB − S_A − S_B) / ln 4`, donde `S_AB` es la entropía de Shannon del espectro mezclado (intensidades sumadas y renormalizadas). Existe un paquete (`ms_entropy`) y `matchms` tiene similitudes de coseno; verifica qué está instalado y su API, y si no está disponible implementa la fórmula y pruébala contra casos conocidos (espectro idéntico → 1).

## Salidas para el ensamble (skill 11)
Por candidato: `a_cos_dreams`, `a_entropy_sim`, `a_rank`, `a_n_matching_spectra`, `a_mass_err_ppm`. **Coseno y entropía son features distintas del ensamble; no se sustituyen entre sí.**

## Verificación
- MRR@25 en Val-Clase1 (skill 04) por semilla; compáralo con la búsqueda clásica por coseno sin DreaMS para cuantificar la ganancia.
- Comprueba que no hay fuga: el espectro *query* no debe estar en el índice.
- **Primer submit temprano:** una línea base con solo el Pilar A valida todo el flujo de entrega (skill 13).
