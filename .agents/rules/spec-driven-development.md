# Agent Rule: Spec-Driven Development (SDD) & Zero "Vibe Coding"
**Path**: `.agents/rules/spec-driven-development.md`  
**Scope**: All AI agents and developers.

## Rule Directives
1. **No Code without Specs**: You must NEVER modify or create files in `src/` without an approved specification in `specs/`.
2. **Order of Operations**:
   - `spec.md`: Formal functional requirements in EARS syntax.
   - `plan.md`: Technical and architectural implementation blueprint.
   - `tasks.md`: Atomic checklist (<30 mins per task) with assigned Dev.
   - `tests/`: Automated unit tests covering edge cases.
   - `src/`: Clean, minimal production implementation that makes the tests pass.
3. **No Unverified Completions**: Never mark a task `[x]` in `tasks.md` without running its corresponding unit tests and observing exit code 0.

