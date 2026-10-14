# Agent Hook: Spec-Sync Enforcement Hook
**Path**: `.agents/hooks/spec-sync-hook.md`  
**Trigger**: Antes de proponer o ejecutar la creación/modificación de cualquier archivo dentro de `src/`.  
**Severity**: Blocking / Mandatory.

---

## Directiva de Ejecución

1. **Condición de Sincronización**:
   Cualquier modificación o creación de archivos en `src/` debe estar explícitamente respaldada por:
   - Una especificación formal en `specs/<feature>/spec.md` (con requisitos EARS identificados).
   - Un plan técnico en `specs/<feature>/plan.md`.
   - Una tarea atómica en `specs/<feature>/tasks.md` en estado pendiente (`- [ ]`).

2. **Acción Bloqueante del Agente**:
   - Si el usuario o el flujo de trabajo solicita editar un archivo en `src/` sin que exista dicha tarea, el agente debe:
     1. Detenerse y advertir: *"Acción bloqueada por spec-sync-hook: No se encontró una especificación activa ni tarea en `specs/` para esta modificación."*
     2. Proponer o generar primero la especificación (`spec.md`), plan (`plan.md`) y tarea (`tasks.md`) correspondiente.
     3. Proceder con el código únicamente tras la validación de la especificación.

3. **Prevención de Vibe Coding**:
   - Este hook neutraliza la improvisación de código, protegiendo las interfaces entre Dev 1, Dev 2 y Dev 3 contra roturas inesperadas.

