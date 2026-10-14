# Skill: Hook Manager
**Path**: `.agents/skills/hook-manager.md`  
**Purpose**: Procedimiento estandarizado para crear, mantener, auditar y verificar hooks de automatización tanto a nivel de Git como del agente de IA.

---

## 1. Clasificación de Hooks en CASMI 2026

El sistema de gobernanza opera en dos capas complementarias:
1. **Git Hooks (`.githooks/`)**: Scripts ejecutables por Git antes de operaciones críticas (`git commit`, `git push`).
2. **Agent Hooks (`.agents/hooks/`)**: Políticas y directivas activas que condicionan el comportamiento de cualquier agente de IA al interactuar con el repositorio.

---

## 2. Gestión de Git Hooks (`.githooks/`)

### 2.1 Activación en el Repositorio
Para que Git ejecute los hooks ubicados en `.githooks/`, debe ejecutarse una única vez por máquina/clon:
```bash
git config core.hooksPath .githooks
```

### 2.2 Hook `pre-commit`
- **Responsabilidad**:
  1. Ejecutar linters rápidos (`ruff check src/ tests/`).
  2. Verificar sintaxis y formato básico (`black --check src/ tests/`).
  3. Ejecutar `python .githooks/check_large_files.py` para bloquear archivos pesados (>50MB, `.parquet`, `.pt`, `.pkl`) que arruinarían el histórico de Git.
- **Salida esperada**: Código de salida `0` si pasa todas las pruebas; código `1` con mensaje descriptivo si falla.

### 2.3 Hook `pre-push`
- **Responsabilidad**:
  1. Ejecutar la suite completa de pruebas unitarias (`pytest tests/ -v`).
  2. Impedir que código roto llegue a las ramas remotas de colaboración entre Dev 1, Dev 2 y Dev 3.
- **Salida esperada**: Bloquea el `push` si cualquier test arroja error o falla.

---

## 3. Gestión de Agent Hooks (`.agents/hooks/`)

### 3.1 Hook `post-task-hook.md`
- **Disparador**: Cada vez que el agente de IA intenta marcar una tarea como completada (`- [x]`) en cualquier `tasks.md`.
- **Acción Obligatoria**: Debe correr el test unitario asociado a la tarea y verificar que pase con éxito (`pytest tests/test_... -v`). Si el test falla o no existe, el agente debe corregir el código o escribir la prueba antes de marcar la casilla.

### 3.2 Hook `spec-sync-hook.md`
- **Disparador**: Cada vez que el agente de IA o un desarrollador intenta modificar o crear archivos en `src/`.
- **Acción Obligatoria**: Verificar que el archivo pertenezca a una especificación activa en `specs/` y a una tarea concreta en `tasks.md`. Previene el "Vibe Coding" y modificaciones no planificadas.

---

## 4. Auditoría y Diagnóstico de Hooks
Para comprobar que los hooks están configurados correctamente:
```bash
# 1. Verificar configuración de hooks de Git
git config --get core.hooksPath
# Salida esperada: .githooks

# 2. Test manual de detector de archivos grandes
python .githooks/check_large_files.py

# 3. Test de suite de pruebas
pytest tests/ -v
```

