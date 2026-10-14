"""Evaluation metrics and chemical standardisation utilities for CASMI 2026.

Replicates the Kaggle evaluation metric (MRR@25) and ground-truth matching
via InChIKey14 tautomer canonicalization using RDKit rdMolStandardize.
"""

import logging
from collections.abc import Sequence

logger = logging.getLogger(__name__)

# Global cached enumerator for RDKit tautomers
_TAUTOMER_ENUMERATOR = None


def get_tautomer_enumerator():
    """Lazily initialize and cache RDKit's TautomerEnumerator."""
    global _TAUTOMER_ENUMERATOR
    if _TAUTOMER_ENUMERATOR is None:
        try:
            from rdkit.Chem.MolStandardize import rdMolStandardize

            _TAUTOMER_ENUMERATOR = rdMolStandardize.TautomerEnumerator()
        except ImportError:
            _TAUTOMER_ENUMERATOR = False
    return _TAUTOMER_ENUMERATOR


def smiles_to_inchikey14(smiles: str) -> str | None:
    """Canonicalize a SMILES string to its first 14-character InChIKey block.

    Follows the official CASMI 2026 rule:
    Prediction and ground truth are canonicalized by tautomers using
    RDKit rdMolStandardize.TautomerEnumerator and reduced to the first InChIKey block.

    Args:
        smiles: 2D SMILES string representation.

    Returns:
        The 14-character InChIKey string (InChIKey14), or None if invalid.
    """
    if not smiles or not isinstance(smiles, str):
        return None

    clean_smiles = smiles.strip()
    if not clean_smiles:
        return None

    try:
        from rdkit import Chem

        mol = Chem.MolFromSmiles(clean_smiles)
        if mol is None:
            return None

        enumerator = get_tautomer_enumerator()
        if enumerator:
            mol = enumerator.Canonicalize(mol)

        inchikey = Chem.MolToInchiKey(mol)
        if inchikey and len(inchikey) >= 14:
            return inchikey[:14]
        return None
    except ImportError:
        # Fallback for environments where rdkit is not yet installed:
        # Generate a deterministic mock hash representation
        import hashlib

        return hashlib.sha256(clean_smiles.encode("utf-8")).hexdigest()[:14].upper()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to canonicalize SMILES '%s': %s", smiles, exc)
        return None


def calculate_mrr_at_25(
    ground_truth_smiles: Sequence[str],
    predicted_candidates: Sequence[Sequence[str]],
    use_inchikey14: bool = True,
) -> float:
    """Calculate Mean Reciprocal Rank @ 25 (MRR@25).

    MRR@25 = (1 / |M|) * sum_{i=1}^{|M|} (1 / rank_i)
    where:
    - rank is 1-indexed (position 1 gives 1.0, position 2 gives 0.5, ..., position 25 gives 0.04).
    - If the correct molecule is not in the top 25 candidates, reciprocal rank is 0.0.
    - Only the FIRST match is counted.

    Args:
        ground_truth_smiles: Ground-truth SMILES for each query molecule.
        predicted_candidates: Ordered list of candidate SMILES (up to 25) for each query molecule.
        use_inchikey14: If True, matches candidates against ground truth by InChIKey14.

    Returns:
        Mean Reciprocal Rank @ 25 as a float between 0.0 and 1.0.
    """
    num_queries = len(ground_truth_smiles)
    if num_queries == 0:
        return 0.0

    total_reciprocal_rank = 0.0

    for gt_smi, candidates in zip(ground_truth_smiles, predicted_candidates):
        if not gt_smi:
            continue

        gt_target = smiles_to_inchikey14(gt_smi) if use_inchikey14 else gt_smi.strip()
        if not gt_target:
            continue

        # Inspect up to top 25 candidates
        matched_rank = 0
        for rank_idx, cand_smi in enumerate(candidates[:25], start=1):
            cand_key = (
                smiles_to_inchikey14(cand_smi)
                if use_inchikey14
                else (cand_smi.strip() if cand_smi else None)
            )
            if cand_key and cand_key == gt_target:
                matched_rank = rank_idx
                break

        if matched_rank > 0:
            total_reciprocal_rank += 1.0 / matched_rank

    return total_reciprocal_rank / num_queries
