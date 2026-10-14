"""Submission generator and validator for CASMI 2026.

Formats top-25 candidate lists into official Kaggle submission.csv format:
molecule_id,smiles
mol_001,CC(=O)Oc1ccccc1C(=O)O;CC(=O)NC1=CC=C(O)C=C1;...
"""

import csv
from collections.abc import Sequence
from pathlib import Path


def format_candidate_string(candidates: Sequence[str], max_k: int = 25) -> str:
    """Format an ordered sequence of candidate SMILES into a semicolon-separated string."""
    cleaned = [c.strip() for c in candidates[:max_k] if c and c.strip()]
    return ";".join(cleaned)


def write_submission_csv(
    predictions_by_molecule: dict[str, Sequence[str]],
    output_path: str | Path = "submission.csv",
    max_candidates: int = 25,
) -> Path:
    """Write predictions dictionary to official submission.csv format.

    Args:
        predictions_by_molecule: Mapping from molecule_id to ordered list of candidate SMILES.
        output_path: Destination path for submission.csv.
        max_candidates: Maximum candidates per row (default 25).

    Returns:
        Path to the generated submission file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["molecule_id", "smiles"])
        for mol_id, candidates in sorted(predictions_by_molecule.items()):
            candidate_str = format_candidate_string(candidates, max_k=max_candidates)
            writer.writerow([mol_id, candidate_str])

    return path


def validate_submission_csv(
    submission_path: str | Path,
    expected_molecule_ids: Sequence[str],
) -> bool:
    """Validate submission.csv format, header, molecule coverage and candidate counts.

    Args:
        submission_path: Path to submission.csv file.
        expected_molecule_ids: List of molecule_ids that must be present.

    Returns:
        True if strictly valid; raises ValueError if any check fails.
    """
    path = Path(submission_path)
    if not path.exists():
        raise FileNotFoundError(f"Submission file not found: {path}")

    seen_molecules = set()
    expected_set = set(expected_molecule_ids)

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != ["molecule_id", "smiles"]:
            raise ValueError(
                f"Invalid header: {header}. Expected ['molecule_id', 'smiles']"
            )

        for line_num, row in enumerate(reader, start=2):
            if len(row) != 2:
                raise ValueError(f"Line {line_num} has {len(row)} columns; expected 2.")
            mol_id, smiles_str = row
            if not mol_id:
                raise ValueError(f"Line {line_num} has empty molecule_id.")
            seen_molecules.add(mol_id)

            candidates = smiles_str.split(";") if smiles_str else []
            if len(candidates) > 25:
                raise ValueError(
                    f"Line {line_num} for molecule {mol_id} exceeds 25 candidates: {len(candidates)}"
                )

    missing = expected_set - seen_molecules
    if missing:
        raise ValueError(
            f"Submission is missing {len(missing)} expected molecule_ids (e.g. {list(missing)[:5]})"
        )

    return True
