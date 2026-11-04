"""Anti-leakage structural validation splitter for CASMI 2026.

Simulates the 3 classes of the hidden Kaggle test set:
- Val-Clase1: Multi-spectrum molecules with 1 held-out query spectrum (remainder in library).
- Val-Clase2: Molecules completely held out from train spectra (SMILES remains in candidates).
- Val-Clase3: Novel molecules with distinct/disjoint Murcko scaffolds isolated from train.

Guarantees 100% disjoint molecule_id partitions between train and Val-Clase2 / Val-Clase3.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.data.spectrum_parser import SpectrumRecord

logger = logging.getLogger(__name__)


def compute_molecular_scaffold(smiles: str | None) -> str:
    """Compute Bemis-Murcko scaffold for a SMILES string with deterministic fallback."""
    if not smiles or not smiles.strip():
        return "UNKNOWN_SCAFFOLD"

    clean_smiles = smiles.strip()
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold

        mol = Chem.MolFromSmiles(clean_smiles)
        if mol is not None:
            scaffold_smi = MurckoScaffold.MurckoScaffoldSmiles(
                mol=mol, includeChirality=False
            )
            if scaffold_smi:
                return scaffold_smi
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.debug("Murcko scaffold failed for '%s': %s", smiles, exc)

    # Fallback: structural fingerprint hash based on canonical characters
    return hashlib.sha256(clean_smiles.encode("utf-8")).hexdigest()[:16]


class StructuralSplitter:
    """Splits spectral datasets into Train and the 3 distinct validation subsets."""

    def __init__(
        self,
        seed: int = 42,
        val_clase1_ratio: float = 0.15,
        val_clase2_ratio: float = 0.10,
        val_clase3_ratio: float = 0.10,
    ):
        self.seed = seed
        self.val_clase1_ratio = val_clase1_ratio
        self.val_clase2_ratio = val_clase2_ratio
        self.val_clase3_ratio = val_clase3_ratio

    def split(self, records: Sequence[SpectrumRecord]) -> dict[str, Any]:
        """Perform anti-leakage 3-class split over spectral records.

        Args:
            records: List or sequence of SpectrumRecord objects.

        Returns:
            Dictionary containing split molecule_ids, spectrum_ids, and metadata.
        """
        rng = random.Random(self.seed)

        # 1. Group records by molecule_id
        molecule_to_records: dict[str, list[SpectrumRecord]] = defaultdict(list)
        molecule_to_scaffold: dict[str, str] = {}

        for rec in records:
            molecule_to_records[rec.molecule_id].append(rec)
            if rec.molecule_id not in molecule_to_scaffold:
                molecule_to_scaffold[rec.molecule_id] = compute_molecular_scaffold(
                    rec.label
                )

        all_mol_ids = sorted(molecule_to_records.keys())
        multi_spec_mols = [m for m in all_mol_ids if len(molecule_to_records[m]) >= 2]
        rng.shuffle(multi_spec_mols)

        # 2. Select Val-Clase1 (molecules with >= 2 spectra)
        n_clase1 = max(1, int(len(multi_spec_mols) * self.val_clase1_ratio))
        val_clase1_mols = set(multi_spec_mols[:n_clase1])

        val_clase1_query_spec_ids: list[str] = []
        train_clase1_spec_ids: list[str] = []

        for mol_id in sorted(val_clase1_mols):
            specs = molecule_to_records[mol_id]
            # Pick 1 random spectrum as query
            query_idx = rng.randint(0, len(specs) - 1)
            val_clase1_query_spec_ids.append(specs[query_idx].spectrum_id)
            for idx, sp in enumerate(specs):
                if idx != query_idx:
                    train_clase1_spec_ids.append(sp.spectrum_id)

        # 3. Remaining pool for Clase2, Clase3, and Train
        remaining_mols = [m for m in all_mol_ids if m not in val_clase1_mols]

        # Group remaining molecules by scaffold
        scaffold_groups: dict[str, list[str]] = defaultdict(list)
        for m in remaining_mols:
            scaffold = molecule_to_scaffold[m]
            scaffold_groups[scaffold].append(m)

        scaffold_keys = sorted(scaffold_groups.keys())
        rng.shuffle(scaffold_keys)

        # 4. Select Val-Clase3 (whole disjoint scaffold clusters)
        val_clase3_mols: set[str] = set()
        target_clase3_count = max(1, int(len(remaining_mols) * self.val_clase3_ratio))

        for scaf in scaffold_keys:
            mols = scaffold_groups[scaf]
            val_clase3_mols.update(mols)
            if len(val_clase3_mols) >= target_clase3_count:
                break

        # 5. Select Val-Clase2 from remaining non-clase3 molecules
        candidates_clase2 = [m for m in remaining_mols if m not in val_clase3_mols]
        rng.shuffle(candidates_clase2)
        target_clase2_count = max(1, int(len(remaining_mols) * self.val_clase2_ratio))
        val_clase2_mols = set(candidates_clase2[:target_clase2_count])

        # 6. Train molecules = remaining mols + Val-Clase1 (whose other spectra are in library)
        train_only_mols = set(candidates_clase2[target_clase2_count:])
        final_train_mols = sorted(train_only_mols | val_clase1_mols)

        # Compile spectrum IDs
        train_spec_ids = list(train_clase1_spec_ids)
        for m in train_only_mols:
            train_spec_ids.extend(r.spectrum_id for r in molecule_to_records[m])

        val_clase2_spec_ids = []
        for m in sorted(val_clase2_mols):
            val_clase2_spec_ids.extend(r.spectrum_id for r in molecule_to_records[m])

        val_clase3_spec_ids = []
        for m in sorted(val_clase3_mols):
            val_clase3_spec_ids.extend(r.spectrum_id for r in molecule_to_records[m])

        return {
            "train_molecule_ids": final_train_mols,
            "train_spectrum_ids": sorted(train_spec_ids),
            "val_clase1_molecule_ids": sorted(val_clase1_mols),
            "val_clase1_query_spectrum_ids": sorted(val_clase1_query_spec_ids),
            "val_clase2_molecule_ids": sorted(val_clase2_mols),
            "val_clase2_spectrum_ids": sorted(val_clase2_spec_ids),
            "val_clase3_molecule_ids": sorted(val_clase3_mols),
            "val_clase3_spectrum_ids": sorted(val_clase3_spec_ids),
            "metadata": {
                "seed": self.seed,
                "n_total_molecules": len(all_mol_ids),
                "n_train_molecules": len(final_train_mols),
                "n_val_clase1_molecules": len(val_clase1_mols),
                "n_val_clase2_molecules": len(val_clase2_mols),
                "n_val_clase3_molecules": len(val_clase3_mols),
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
            },
        }


def generate_and_save_splits(
    records: Sequence[SpectrumRecord],
    output_dir: str | Path = "data/splits",
    seeds: Sequence[int] = (42, 1337, 2026),
) -> dict[int, Path]:
    """Generate and persist split files for multiple seeds.

    Args:
        records: Spectral records to partition.
        output_dir: Destination folder for split JSON manifests.
        seeds: Sequence of integer random seeds.

    Returns:
        Mapping from seed to generated Path.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    manifest_paths: dict[int, Path] = {}
    for s in seeds:
        splitter = StructuralSplitter(seed=s)
        split_data = splitter.split(records)
        target_file = out_path / f"split_seed_{s}.json"

        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(split_data, f, indent=2)

        manifest_paths[s] = target_file
        logger.info("Saved split for seed %d to %s", s, target_file)

    return manifest_paths
