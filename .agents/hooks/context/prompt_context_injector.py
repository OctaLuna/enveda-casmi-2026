#!/usr/bin/env python3
"""
H02 - prompt-context-injector
Interpreta la intención del prompt del usuario o agente y provee recordatorios contextuales
de los invariantes críticos de Enveda CASMI 2026.
"""

from pathlib import Path
import re
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()
    prompt = (payload.get("prompt") or "").lower()

    if not prompt:
        sys.exit(0)

    reminders = []

    # 1. Submission / Kaggle Final
    if any(k in prompt for k in ["submit", "enviar", "leaderboard", "submission", "notebook final", "entrega"]):
        reminders.append(
            "[RECORDATORIO SUBMISSION CASMI 2026]\n"
            "  - Formato: submission.csv con columnas exactas (molecule_id, smiles)\n"
            "  - Máximo 25 SMILES por fila, ordenados de mayor a menor probabilidad, separados por ';'\n"
            "  - Límite de cómputo estricto: 9 horas. Modo de evaluación: CERO INTERNET\n"
            "  - Reporta siempre MRR@25 local por clase antes de hacer release."
        )

    # 2. Particiones / Validación
    if any(k in prompt for k in ["split", "validacion", "validación", "cv", "kfold", "leakage"]):
        reminders.append(
            "[RECORDATORIO VALIDACIÓN ANTI-LEAKAGE]\n"
            "  - Partición obligatoria por 'molecule_id', NUNCA por 'spectrum_id'\n"
            "  - Agrupamiento estructural con Murcko Scaffolds / MCES para aislar Val-Clase3\n"
            "  - Evalúa siempre sobre al menos 3 semillas deterministas (min_seeds=3)."
        )

    # 3. Canonicalización / Chemoinformatics
    if any(k in prompt for k in ["rdkit", "canonical", "tautomer", "tautómero", "inchikey", "smiles"]):
        reminders.append(
            "[RECORDATORIO QUIMIOINFORMÁTICA CASMI]\n"
            "  - Versión fija de RDKit: 2026.03.3\n"
            "  - Canonicalizador: rdMolStandardize.TautomerEnumerator()\n"
            "  - Comparación en Kaggle: primer bloque del InChIKey (InChIKey14)."
        )

    if reminders:
        print("\n" + "\n\n".join(reminders) + "\n")

    sys.exit(0)


if __name__ == "__main__":
    main()

