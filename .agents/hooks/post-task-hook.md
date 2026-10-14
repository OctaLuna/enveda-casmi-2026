# Agent Hook: Post-Task Verification Hook
**Path**: `.agents/hooks/post-task-hook.md`  
**Trigger**: Antes de marcar una casilla como completada (`- [x]`) en cualquier archivo `tasks.md` de `specs/`.  
**Severity**: Blocking / Mandatory.

---

## Directiva de Ejecución

1. **Condición Previa**:
   El agente de IA o desarrollador tiene **estrictamente prohibido** marcar una tarea como completada (`- [x]`) si:
   - No existe una prueba unitaria o de integración correspondiente en el directorio `tests/`.
   - La suite de pruebas no ha sido ejecutada en la misma sesión y verificado su código de salida exitoso (`0`).

2. **Protocolo del Agente**:
   Antes de editar `tasks.md` para marcar `[x]`:
   ```bash
   # Paso 1: Ejecutar la prueba específica de la tarea
   pytest tests/test_<modulo_asociado>.py -v

   # Paso 2: Si el test falla, DETENERSE, corregir la implementación en src/ y re-ejecutar.
   # Paso 3: Solo cuando el output indique "PASSED", proceder a actualizar tasks.md.
   ```

3. **Registro de Auditoría**:
   En el commit o resumen de turno, el agente debe reportar el comando ejecutado y la confirmación del paso exitoso del test.

