"""Métrica MRR@25 y canonicalización InChIKey14 para CASMI 2026.

Replica la descripción del evaluador: tautómero canónico (RDKit rdMolStandardize)
-> InChIKey -> primer bloque (InChIKey14). Verifica la versión de RDKit.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Optional

import rdkit
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchiKey
from rdkit.Chem.MolStandardize import rdMolStandardize

EXPECTED_RDKIT = "2026.3.3"  # el masterplan escribe 2026.03.3

_enum = rdMolStandardize.TautomerEnumerator()


def check_rdkit_version(expected: str = EXPECTED_RDKIT) -> bool:
    """Devuelve True si coincide la versión. Imprime aviso si no."""
    norm = lambda v: ".".join(str(int(p)) for p in v.split("."))
    ok = norm(rdkit.__version__) == norm(expected)
    if not ok:
        print(f"[AVISO] RDKit {rdkit.__version__} != esperado {expected}. "
              "El MRR local puede no correlacionar con el leaderboard.")
    return ok


@lru_cache(maxsize=2_000_000)
def inchikey14(smiles: str) -> Optional[str]:
    """SMILES -> tautómero canónico -> InChIKey -> primer bloque. None si falla."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        mol = _enum.Canonicalize(mol)
        return MolToInchiKey(mol).split("-")[0]
    except Exception:
        return None


def dedupe_topk(candidates: Iterable[str], k: int = 25) -> List[str]:
    """Elimina inválidos y duplicados por InChIKey14, conserva orden, corta a k."""
    seen, out = set(), []
    for smi in candidates:
        key = inchikey14(smi)
        if key is None or key in seen:
            continue
        seen.add(key)
        out.append(smi)
        if len(out) == k:
            break
    return out


def mrr_at_k(preds: Dict[str, List[str]], truth: Dict[str, str], k: int = 25) -> float:
    """MRR@k. preds: molecule_id -> lista ordenada de SMILES; truth: molecule_id -> SMILES real."""
    total = 0.0
    for mol_id, true_smi in truth.items():
        true_key = inchikey14(true_smi)
        ranked = dedupe_topk(preds.get(mol_id, []), k)
        for rank, smi in enumerate(ranked, start=1):
            if inchikey14(smi) == true_key:
                total += 1.0 / rank
                break
    return total / max(len(truth), 1)


def selftest() -> None:
    """Pruebas mínimas: tautómeros equivalentes y estereo ignorada."""
    check_rdkit_version()
    # Estereo ignorada (InChIKey14 no codifica estereo)
    assert inchikey14("C[C@H](N)C(=O)O") == inchikey14("C[C@@H](N)C(=O)O")
    # Tautómeros ceto/enol de la acetona
    assert inchikey14("CC(C)=O") == inchikey14("CC(O)=C")
    assert mrr_at_k({"a": ["CCO", "CC(C)=O"]}, {"a": "CC(C)=O"}) == 0.5
    print("selftest OK")


if __name__ == "__main__":
    selftest()
