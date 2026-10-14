# Regla Agéntica: Inferencia Offline en Kaggle
**Ubicación**: `.agents/rules/offline-inference.md`  
**Refuerzo Automático**: Hook `H14`.

La evaluación final del notebook de sumisión en Kaggle se ejecuta en un contenedor con **acceso a internet totalmente deshabilitado**.

1. **Prohibición de Red [H14]**:
   - Queda terminantemente prohibido el uso de `requests`, `urllib`, `wget`, `gdown`, `git clone` o descargas dinámicas vía `huggingface_hub` en los scripts de inferencia (`inference/`, `notebooks/final/`, `src/inference/`, `src/api/`).
2. **Carga de Modelos y Pesos [H28]**:
   - Todo modelo (DreaMS, MIST, DiffMS, CFM-ID, LightGBM) debe cargarse exclusivamente desde rutas de datasets de Kaggle montadas localmente (`/kaggle/input/...` o `models/`).
   - Todos los artefactos deben estar registrados en `kaggle/manifest.yaml` con su versión y hash SHA-256.
3. **Instalación de Paquetes**:
   - Las dependencias adicionales deben suministrarse como `.whl` locales empaquetados previamente en datasets offline.
