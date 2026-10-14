# Workflow: /pre-pr
**Propósito**: Preparar y validar la rama de trabajo antes de abrir un Pull Request hacia `develop`.

## Pasos de Ejecución:
1. **Ejecutar Verificaciones de Pre-Push**:
   ```bash
   python .agents/bin/run_checks.py pre-push
   ```
2. **Confirmar Ausencia de Conflictos con develop**:
   ```bash
   git fetch origin develop
   git merge origin/develop
   ```
3. **Completar Plantilla de Pull Request**:
   Diligenciar los campos requeridos en `.github/pull_request_template.md`:
   - Clases moleculares impactadas (Clase 1, 2 y/o 3).
   - Tabla de MRR@25 antes vs. después con 3 semillas.
   - Impacto en el presupuesto de cómputo (minutos agregados).
   - Fuentes de datos externas utilizadas y estado de sus licencias.
   - Declaración de conformidad offline (cero llamadas a red).
