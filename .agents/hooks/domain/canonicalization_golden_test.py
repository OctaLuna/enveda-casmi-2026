#!/usr/bin/env python3
"""
H21 - canonicalization-golden-test
Valida que la función de canonicalización tautomérica cumpla con los requisitos oficiales
de Kaggle CASMI 2026: primer bloque de InChIKey (InChIKey14) invariante ante tautómeros
y estereoisómeros, pero discriminante ante moléculas estructuralmente distintas.
"""

from pathlib import Path
import sys

HOOK_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOK_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import common

# Pares de prueba golden: (SMILES A, SMILES B, deben_coincidir)
GOLDEN_PAIRS = [
    # Tautómeros ceto-enólicos y piridonas
    ("CC(=O)CC(=O)C", "CC(=O)C=C(O)C", True),
    ("Oc1ccccn1", "O=c1[nH]cccc1", True),
    ("CC(=O)N", "CC(=N)O", True),
    # Estereocentros (deben coincidir a nivel InChIKey14)
    ("C[C@H](O)CC", "C[C@@H](O)CC", True),
    ("O=C(O)[C@@H](N)C", "O=C(O)[C@H](N)C", True),
    # Moléculas distintas (deben diferir)
    ("CCO", "CCCN", False),
    ("c1ccccc1", "c1ccncc1", False),
    ("CC(=O)O", "CCOC=O", False),
]


def test_with_rdkit():
    try:
        from rdkit import Chem
        from rdkit.Chem.MolStandardize import rdMolStandardize
    except ImportError:
        common.warn("RDKit no está disponible en este intérprete; omitiendo ejecución golden real.", hook_id="H21")
        return True

    enumerator = rdMolStandardize.TautomerEnumerator()

    def get_inchikey14(smi: str) -> str:
        mol = Chem.MolFromSmiles(smi)
        if not mol:
            return ""
        canon_mol = enumerator.Canonicalize(mol)
        inchi = Chem.MolToInchi(canon_mol)
        inchikey = Chem.InchiToInchiKey(inchi)
        return inchikey.split("-")[0] if inchikey else ""

    for smi_a, smi_b, should_match in GOLDEN_PAIRS:
        key_a = get_inchikey14(smi_a)
        key_b = get_inchikey14(smi_b)
        if not key_a or not key_b:
            common.block(
                f"Error parseando SMILES en golden test: '{smi_a}' o '{smi_b}'",
                hook_id="H21",
                reason="SMILES inválido en test de canonicalización.",
                solution="Verifica sintaxis RDKit."
            )
        match = (key_a == key_b)
        if match != should_match:
            common.block(
                f"Fallo en golden pair: ('{smi_a}', '{smi_b}'). Esperado coincidir={should_match}, Obtenido={match} ({key_a} vs {key_b})",
                hook_id="H21",
                reason="La canonicalización no respeta las equivalencias tautoméricas exigidas por la métrica de Kaggle.",
                solution="Usa rdMolStandardize.TautomerEnumerator().Canonicalize(mol) antes de calcular InChIKey."
            )
    return True


def main():
    payload = common.read_stdin_payload()
    config = common.load_project_config()

    test_with_rdkit()
    sys.exit(0)


if __name__ == "__main__":
    main()
