# Skill: Git Branching, Commit Protocol & AI Agent Collaboration
**Path**: `.agents/skills/git-branching-commit.md`  
**Destinatarios**: Octavio Luna (Dev 1), Leonardo Ibarra (Dev 2), Joan Riveros (Dev 3) y sus Agentes de IA (Antigravity, Claude Code, Cursor, Copilot).

---

## 1. Topología de Ramas del Repositorio

El proyecto utiliza un modelo de integración continua adaptado a Machine Learning colaborativo para 3 desarrolladores sin bloqueos:

```
[ main ]          <-- Producción congelada / Envíos oficiales Kaggle (Protegida)
   ^
   |
[ develop ]       <-- Rama de integración continua de features completadas (Protegida)
   ^
   |
[ test ]          <-- Banco de pruebas de estrés, evaluación offline y límite 9h
   ^
   |
+--+------------------------+----------------------+
|                           |                      |
[ octavio ]           [ leonardo ]           [ joan ]
(Octavio Luna)        (Leonardo Ibarra)      (Joan Riveros)
       |                     |                      |
       v                     v                      v
feature/sprint1-octavio-splitter   feature/sprint2-leonardo-faiss   feature/sprint3-joan-diffms
```

### Propósito y Reglas de Cada Rama
| Rama | Descripción | Política de Acceso |
|---|---|---|
| **`main`** | Código de producción final, estable y empaquetado para Kaggle. | **Estrictamente protegida**. Solo merges desde `develop` vía PR validado. |
| **`develop`** | Integración continua donde convergen las features completadas del Sprint. | **Estrictamente protegida**. Requiere tests verdes y aprobación cruzada. |
| **`test`** | Banco de pruebas de estrés y simulación offline para medir tiempos ($\le 9\text{h}$) y VRAM/RAM. | Integración y benchmark previo a release. |
| **`product`** | Entorno de congelamiento y preparación del artefacto Kaggle final. | Staging de entrega. |
| **`octavio`** | Espacio de trabajo e integración de **Octavio Luna** (Datos y Validación). | Libre para Dev 1 y su agente de IA. |
| **`leonardo`** | Espacio de trabajo e integración de **Leonardo Ibarra** (Retrieval y MIST). | Libre para Dev 2 y su agente de IA. |
| **`joan`** | Espacio de trabajo e integración de **Joan Riveros** (De Novo y Ensamble). | Libre para Dev 3 y su agente de IA. |
| **`feature/*`** | Ramas efímeras creadas a partir de `develop` o `<dev>` para una tarea atómica SDD. | Se eliminan tras el merge exitoso. |

---

## 2. Convención Estricta de Commits: Conventional Commits en ESPAÑOL

> **Regla de Oro Innegociable**: Todos los mensajes de commit generados tanto por desarrolladores humanos como por Agentes de IA deben redactarse obligatoriamente en **ESPAÑOL**, siguiendo el formato estándar de *Conventional Commits*:

```text
<tipo>(<ámbito>): <descripción concisa en imperativo y en minúsculas>

[cuerpo explicativo opcional: justificación técnica o contexto]

[referencia opcional a requisito o tarea: ej. RF: REQ-EVT-01, Tarea: DEV1-T2.1]
```

### Tipos de Commit Permitidos (con ejemplos en Español)
* **`feat`**: Nueva funcionalidad técnica en datos, modelos o pipelines.
  * *Ejemplo*: `feat(datos): implementar deisotopado explicito de espectros ms2`
  * *Ejemplo*: `feat(retrieval): indexar embeddings dreams en faiss ivf-pq`
* **`fix`**: Corrección de un error, bug o discrepancia numérica.
  * *Ejemplo*: `fix(metrica): corregir canonicalizacion de tautomeros en inchikey14`
  * *Ejemplo*: `fix(adductos): ajustar tabla de masas monoisotopicas para [m+fa-h]-`
* **`test`**: Creación o actualización de pruebas unitarias o de integración en `tests/`.
  * *Ejemplo*: `test(reproducibilidad): agregar pruebas de determinismo de semillas`
  * *Ejemplo*: `test(submision): verificar validacion de formato submission.csv`
* **`refactor`**: Reestructuración de código sin alterar su comportamiento externo ni API.
  * *Ejemplo*: `refactor(parser): vectorizar filtrado de intensidades relativas`
* **`perf`**: Optimizaciones directas de velocidad de cómputo, latencia o consumo de memoria.
  * *Ejemplo*: `perf(cascada): reducir presupuesto de inferencia a 35s por molecula`
* **`docs`**: Modificaciones en documentación técnica, especificaciones SDD o actas SCRUM.
  * *Ejemplo*: `docs(scrum): actualizar nombres de desarrolladores y topologia de ramas`
  * *Ejemplo*: `docs(sdd): agregar limites de alcance a especificacion 001`
* **`chore`**: Tareas rutinarias de configuración, linters, hooks o dependencias.
  * *Ejemplo*: `chore(hooks): activar verificacion de archivos mayores a 50mb`

---

## 3. Protocolo de Trabajo para los Desarrolladores y sus Agentes de IA

### Paso 1: Iniciar una Nueva Tarea SDD
1. Localizar la tarea en `specs/.../tasks.md`.
2. Actualizar la rama base desde GitHub:
   ```bash
   git checkout develop
   git pull origin develop
   ```
3. Crear rama de trabajo personal o de feature:
   ```bash
   # Opción recomendada por tarea:
   git checkout -b feature/sprint1-octavio-deisotopado

   # O trabajar en la rama personal del desarrollador:
   git checkout octavio
   git merge develop
   ```

### Paso 2: Desarrollo Test-First (TDD)
1. Escribir primero la prueba en `tests/test_<modulo>.py`.
2. Implementar la funcionalidad en `src/<modulo>/`.
3. Ejecutar y verificar la prueba:
   ```bash
   pytest tests/test_<modulo>.py -v
   ```

### Paso 3: Verificación Previa al Commit
Antes de hacer commit, el agente o desarrollador debe verificar:
```bash
# 1. Linters y formateadores
ruff check src/ tests/
black --check src/ tests/

# 2. Suite de pruebas pasando al 100%
pytest tests/ -v

# 3. Detector de archivos pesados (>50MB, .parquet, .pt)
python .githooks/check_large_files.py
```

### Paso 4: Creación del Commit (en Español)
```bash
git add src/ tests/
git commit -m "feat(datos): implementar particion disjunta por molecule_id [RF: REQ-EVT-03]"
git push origin <mi-rama>
```
*(El Git Hook `pre-push` se ejecutará automáticamente validando pytest antes de autorizar el push).*

### Paso 5: Pull Request hacia `develop`
* Abrir el PR en GitHub hacia la rama `develop`.
* Solicitar revisión cruzada entre integrantes (Octavio $\leftrightarrow$ Leonardo $\leftrightarrow$ Joan).
* Solo tras la aprobación y verificación del CI se realiza el merge.

---

## 4. Mandamientos para los Agentes de IA (Zero Conflict Directive)

1. **Idiomas de Commits**: Todo commit redactado por un agente de IA **DEBE SER EN ESPAÑOL**. Queda prohibido generar mensajes en inglés (`feat: add...` $\rightarrow$ debe ser `feat: agregar...` o `feat(modulo): implementar...`).
2. **Prohibido Push Forzado**: Ningún agente de IA puede ejecutar `git push --force` o `git push -f`.
3. **Respeto a los Git Hooks**: Prohibido usar el flag `--no-verify`. Si un hook falla, el agente debe corregir el código.
4. **Respeto de Dominios de Código**:
   - Agente de Octavio no modifica `src/models/` directamente.
   - Agente de Leonardo no modifica `src/data/` ni `src/api/` directamente.
   - Agente de Joan no modifica `src/models/retrieval/` directamente.
   - Todo cambio de interfaz compartida debe plasmarse en `specs/` antes de codificar.
