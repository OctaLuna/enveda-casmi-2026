"""Valida submission.csv de CASMI 2026.

Uso:
    python validate_submission.py --submission submission.csv --sample sample_submission.csv

Comprueba: mismas columnas que el sample, una fila por molecule_id del sample,
máx. 25 SMILES separados por ';', sin vacíos, sin duplicados por InChIKey14,
y SMILES válidos (si RDKit está disponible).
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

try:
    from rdkit import Chem
    from rdkit.Chem.inchi import MolToInchiKey
    HAVE_RDKIT = True
except Exception:  # pragma: no cover
    HAVE_RDKIT = False


def key14(smi: str):
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None
    try:
        return MolToInchiKey(mol).split("-")[0]
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--max-k", type=int, default=25)
    args = ap.parse_args()

    sub = pd.read_csv(args.submission, dtype=str)
    smp = pd.read_csv(args.sample, dtype=str)
    errors, warns = [], []

    if list(sub.columns) != list(smp.columns):
        errors.append(f"Columnas distintas: {list(sub.columns)} vs sample {list(smp.columns)}")
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1

    id_col, pred_col = smp.columns[0], smp.columns[1]
    if sub[id_col].duplicated().any():
        errors.append(f"IDs duplicados en '{id_col}': {int(sub[id_col].duplicated().sum())}")
    missing = set(smp[id_col]) - set(sub[id_col])
    extra = set(sub[id_col]) - set(smp[id_col])
    if missing:
        errors.append(f"Faltan {len(missing)} molecule_id (p. ej. {sorted(missing)[:3]})")
    if extra:
        errors.append(f"Sobran {len(extra)} molecule_id (p. ej. {sorted(extra)[:3]})")

    n_short = 0
    for mol_id, cell in zip(sub[id_col], sub[pred_col]):
        if not isinstance(cell, str) or not cell.strip():
            errors.append(f"{mol_id}: predicciones vacías")
            continue
        smiles = [s.strip() for s in cell.split(";")]
        if any(s == "" for s in smiles):
            errors.append(f"{mol_id}: elemento vacío (¿';' sobrante?)")
        if len(smiles) > args.max_k:
            errors.append(f"{mol_id}: {len(smiles)} candidatos (> {args.max_k})")
        if len(smiles) < args.max_k:
            n_short += 1
        if HAVE_RDKIT:
            keys = [key14(s) for s in smiles if s]
            if any(k is None for k in keys):
                errors.append(f"{mol_id}: SMILES inválido")
            valid = [k for k in keys if k is not None]
            if len(valid) != len(set(valid)):
                warns.append(f"{mol_id}: duplicados por InChIKey14 (desperdician posiciones)")
    if n_short:
        warns.append(f"{n_short} moléculas con < {args.max_k} candidatos (se pierde recall potencial)")
    if not HAVE_RDKIT:
        warns.append("RDKit no disponible: no se validaron SMILES ni duplicados")

    for w in warns:
        print(f"AVISO: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print("RESULTADO:", "FALLA" if errors else "OK", f"({len(sub)} filas)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

