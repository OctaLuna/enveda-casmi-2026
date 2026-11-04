"""Offline candidate molecular database partitioned by exact formula for CASMI 2026.

Provides O(1) in-memory lookup by molecular formula (Hill system),
consolidates multiple public sources (PubChem, COCONUT, LOTUS, HMDB) with InChIKey14 deduplication,
and enables high-performance Parquet serialization.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.utils.metrics import smiles_to_inchikey14

logger = logging.getLogger(__name__)


def smiles_to_formula_and_mass(
    smiles: str,
) -> tuple[str | None, float | None]:
    """Calculate Hill molecular formula and exact monoisotopic mass from SMILES."""
    if not smiles or not smiles.strip():
        return None, None

    try:
        from rdkit import Chem
        from rdkit.Chem import rdMolDescriptors

        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return None, None

        formula = rdMolDescriptors.CalcMolFormula(mol)
        exact_mass = float(rdMolDescriptors.CalcExactMolWt(mol))
        return formula, exact_mass
    except ImportError:
        logger.debug("RDKit unavailable for formula calculation from SMILES")
        return None, None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Error computing formula for '%s': %s", smiles, exc)
        return None, None


@dataclass
class CandidateRecord:
    """Represents a unique candidate molecular structure in the reference universe."""

    inchikey14: str
    smiles: str
    formula: str
    exact_mass: float
    sources: list[str]


class CandidateDatabase:
    """In-memory formula-partitioned molecular candidate database."""

    def __init__(self):
        self._by_formula: dict[str, list[CandidateRecord]] = defaultdict(list)
        self._by_inchikey14: dict[str, CandidateRecord] = {}

    @property
    def size(self) -> int:
        """Total number of unique molecular structures in the database."""
        return len(self._by_inchikey14)

    def add_candidate(
        self,
        smiles: str,
        source: str = "Unknown",
        formula: str | None = None,
        exact_mass: float | None = None,
    ) -> CandidateRecord | None:
        """Add or merge a candidate molecule into the database.

        If a molecule with the same InChIKey14 already exists, its source set is updated.

        Args:
            smiles: 2D SMILES string.
            source: Name of reference database (e.g. 'PubChem', 'COCONUT', 'LOTUS').
            formula: Optional precomputed Hill formula.
            exact_mass: Optional precomputed monoisotopic mass.

        Returns:
            The created or updated CandidateRecord, or None if SMILES is unparseable.
        """
        key14 = smiles_to_inchikey14(smiles)
        if not key14:
            return None

        clean_smi = smiles.strip()

        # If already indexed, merge sources
        if key14 in self._by_inchikey14:
            existing = self._by_inchikey14[key14]
            if source and source not in existing.sources:
                existing.sources.append(source)
                existing.sources.sort()
            return existing

        # Derive formula and mass if not provided
        if not formula or exact_mass is None:
            calc_formula, calc_mass = smiles_to_formula_and_mass(clean_smi)
            formula = formula or calc_formula
            exact_mass = exact_mass if exact_mass is not None else calc_mass

        if not formula or exact_mass is None:
            logger.debug(
                "Could not determine formula/mass for candidate '%s'", clean_smi
            )
            return None

        record = CandidateRecord(
            inchikey14=key14,
            smiles=clean_smi,
            formula=formula,
            exact_mass=exact_mass,
            sources=[source] if source else ["Unknown"],
        )

        self._by_inchikey14[key14] = record
        self._by_formula[formula].append(record)
        return record

    def add_candidates_batch(
        self,
        candidates: Sequence[tuple[str, str]],
    ) -> int:
        """Batch ingestion of (smiles, source) pairs.

        Returns:
            Count of successfully processed candidates.
        """
        count = 0
        for smi, src in candidates:
            if self.add_candidate(smi, source=src) is not None:
                count += 1
        return count

    def get_candidates(self, formula: str) -> list[CandidateRecord]:
        """Query candidates matching exact Hill molecular formula in O(1) time.

        Args:
            formula: Hill notation molecular formula (e.g. 'C8H10N4O2').

        Returns:
            List of CandidateRecord objects matching the given formula.
        """
        return self._by_formula.get(formula.strip(), [])

    def save_to_parquet(self, path: str | Path) -> Path:
        """Serialize candidate database to high-performance Parquet format.

        Args:
            path: Target file destination.

        Returns:
            Path to written Parquet file.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        keys14 = []
        smiles_list = []
        formulas = []
        masses = []
        sources_list = []

        for rec in self._by_inchikey14.values():
            keys14.append(rec.inchikey14)
            smiles_list.append(rec.smiles)
            formulas.append(rec.formula)
            masses.append(rec.exact_mass)
            sources_list.append(rec.sources)

        table = pa.Table.from_arrays(
            [
                pa.array(keys14, type=pa.string()),
                pa.array(smiles_list, type=pa.string()),
                pa.array(formulas, type=pa.string()),
                pa.array(masses, type=pa.float64()),
                pa.array(sources_list, type=pa.list_(pa.string())),
            ],
            names=[
                "inchikey14",
                "smiles",
                "formula",
                "exact_mass",
                "sources",
            ],
        )

        pq.write_table(table, dest, compression="snappy")
        logger.info("Saved %d candidate molecules to %s", len(keys14), dest)
        return dest

    @classmethod
    def load_from_parquet(cls, path: str | Path) -> CandidateDatabase:
        """Instantiate and populate CandidateDatabase from a Parquet file.

        Args:
            path: Path to serialized Parquet file.

        Returns:
            Populated CandidateDatabase instance.
        """
        source_path = Path(path)
        if not source_path.exists():
            raise FileNotFoundError(
                f"Candidate database Parquet not found: {source_path}"
            )

        db = cls()
        table = pq.read_table(source_path)
        pydict = table.to_pydict()

        n_rows = len(pydict["inchikey14"])
        for i in range(n_rows):
            rec = CandidateRecord(
                inchikey14=str(pydict["inchikey14"][i]),
                smiles=str(pydict["smiles"][i]),
                formula=str(pydict["formula"][i]),
                exact_mass=float(pydict["exact_mass"][i]),
                sources=[str(s) for s in pydict["sources"][i]],
            )
            db._by_inchikey14[rec.inchikey14] = rec
            db._by_formula[rec.formula].append(rec)

        logger.info("Loaded %d candidate molecules from %s", db.size, source_path)
        return db
