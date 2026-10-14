# Regla Agéntica: Protección de Datos Crudos y Credenciales
**Ubicación**: `.agents/rules/datos-protegidos.md`  
**Refuerzo Automático**: Hooks `H10`, `H11`, `H12`, `H29`.

1. **Inmutabilidad de Datos Crudos [H11]**:
   - `data/raw/` (`train.parquet`, `test.parquet`, `sample_submission.csv`) no debe ser alterado, renombrado ni borrado.
   - Prohibido el uso de `rm -rf` sobre directorios de datos o pesos.
2. **Cero Secretos y Credenciales en Git [H10]**:
   - Prohibido commitear `kaggle.json`, variables `.env` o tokens de API (`ghp_`, `github_pat_`, AWS keys).
   - Prohibido emitir comandos de terminal que vuelquen el contenido de `~/.kaggle/kaggle.json`.
3. **Control de Archivos Pesados [H12]**:
   - Límite estricto de 25 MB por archivo en Git. Extensiones prohibidas en el repo: `.parquet`, `.pt`, `.ckpt`, `.safetensors`, `.faiss`, `.index`.
4. **Trazabilidad de Licencias Comerciales [H29]**:
   - Toda fuente de datos externa debe registrarse en `docs/DATA_SOURCES.md`. En la rama `main` no se permiten fuentes con licencia "Por verificar".

