# Skill: SDD Spec Generator (Spec-Driven Development)
**Path**: `.agents/skills/sdd-spec-generator.md`  
**Purpose**: Guía de procedimiento para formular especificaciones técnicas rigurosas utilizando la sintaxis EARS y desglosar planes de implementación con tareas atómicas.

---

## 1. El Trinomio SDD
Cada funcionalidad, módulo o modelo nuevo en el repositorio debe residir en `specs/<id>_<nombre>/` y contener tres artefactos sincronizados:
1. `spec.md`: Especificación de requisitos formales funcionales y no funcionales en sintaxis EARS.
2. `plan.md`: Arquitectura técnica, contratos de interfaz, prevención de riesgos y métricas.
3. `tasks.md`: Lista de tareas atómicas (20-30 minutos) con checkboxes `[ ]`, dependencias y asignación a Dev 1, Dev 2 o Dev 3.

---

## 2. Sintaxis EARS (Easy Approach to Requirements Syntax)

Los requisitos funcionales deben redactarse siguiendo estrictamente uno de los 5 patrones EARS:

| Patrón EARS | Estructura Sintáctica | Ejemplo en CASMI |
|---|---|---|
| **Ubiquitous (General)** | El sistema debe `<acción>` | El sistema debe normalizar las intensidades espectrales al pico base = 1.0. |
| **Event-Driven (Evento)** | CUANDO `<evento>`, el sistema debe `<acción>` | CUANDO el preprocesador detecte un fragmento con masa $> \text{precursor\_mz} + 2.0\text{ Da}$, el sistema debe descartar dicho fragmento. |
| **State-Driven (Estado)** | MIENTRAS `<estado>`, el sistema debe `<acción>` | MIENTRAS el proceso de inferencia esté en ejecución bajo modo Kaggle offline, el sistema debe utilizar los pesos locales sin realizar llamadas a red. |
| **Unwanted Behavior (Error)** | SI `<condición anómala>`, ENTONCES el sistema debe `<acción>` | SI un espectro contiene menos de 5 picos válidos, ENTONCES el pipeline debe emitir una advertencia estructurada y descartar el espectro del split de entrenamiento. |
| **Optional (Opcional)** | DONDE `<característica opcional>`, el sistema debe `<acción>` | DONDE se disponga de múltiples energías de colisión para una misma molécula, el sistema debe fusionar los embeddings DreaMS ponderando por número de picos. |

---

## 3. Estructura de `plan.md`
- **Resumen Arquitectónico**: Diagrama de componentes y contratos de entrada/salida.
- **Elección Tecnológica & Modelado**: Justificación de modelos, algoritmos o estructuras de datos.
- **Prevención de Data Leakage**: Definición explícita del aislamiento entre train y validation.
- **Esquema de Evaluación**: Definición de métrica MRR@25 y evaluación en los 3 subsets.
- **Presupuesto de Cómputo**: Tiempo estimado de CPU/GPU y memoria RAM/VRAM.

---

## 4. Desglose de `tasks.md`
- **Atomicidad**: Cada tarea debe completarse en 20 a 30 minutos.
- **Formato Requerido**:
  `- [ ] [DEV-ID] [MOD-ID] Tarea concreta con definición de completitud (DoD)`
- **Dependencias**: Indicar explícitamente si una tarea depende de otra (ej. `(Bloqueada por Task 1.2)`).
- **Protocolo de Cierre**: Prohibido marcar `[x]` si el test unitario asociado no ha sido escrito y ejecutado con éxito (`pytest tests/test_... -v`).
