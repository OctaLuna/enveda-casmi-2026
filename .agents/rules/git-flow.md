# Regla Agéntica: Flujo de Git y Nomenclatura de Ramas
**Ubicación**: `.agents/rules/git-flow.md`  
**Refuerzo Automático**: Hooks Git `G01`, `G02`, `G03`, `G04`, `G05`, `G06`.

1. **Ramas Principales Protegidas [G04]**:
   - `main`: Código final y submissions oficiales. Prohibido hacer push directo.
   - `develop`: Integración continua de sprints. Requiere PR con revisión y tests en verde.
2. **Ramas Personales y de Trabajo**:
   - `octavio` (Octavio Luna): Datos, splits y métricas.
   - `leonardo` (Leonardo Ibarra): Retrieval y predicción de fingerprints.
   - `joan` (Joan Riveros): Modelos de novo y ensamble.
   - Feature branches: `(feat|fix|exp|chore|docs)/<nombre-en-minusculas>`.
3. **Mensajes de Commit en Español y Conventional Commits [G02]**:
   - Estructura: `<tipo>(<scope>): <descripción concisa en imperativo y minúsculas>`.
   - Tipos: `feat`, `fix`, `exp`, `perf`, `refactor`, `test`, `docs`, `chore`, `ci`.
   - Scopes: `pilar-a`, `pilar-b`, `pilar-c`, `ensemble`, `val`, `prep`, `infra`, `docs`, `kaggle`, `agent`, `datos`, `metrica`, `reproducibilidad`.
