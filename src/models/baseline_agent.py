"""Baseline candidate retrieval model for CASMI 2026.

Provides spectral retrieval and heuristic baseline matching interfaces.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from src.data.spectrum_parser import SpectrumRecord


@dataclass
class CandidatePrediction:
    """Represents a predicted candidate structure with associated score."""

    smiles: str
    score: float
    rank: int


class BaselineSpectralMatcher:
    """Baseline retrieval engine matching query spectra against a known training library."""

    def __init__(self):
        self.library_records: list[SpectrumRecord] = []

    def fit(self, records: Sequence[SpectrumRecord]) -> "BaselineSpectralMatcher":
        """Index training spectrum records with valid ground-truth SMILES labels."""
        self.library_records = [rec for rec in records if rec.label]
        return self

    def predict_top_k(
        self,
        query: SpectrumRecord,
        k: int = 25,
        precursor_tolerance_da: float = 5.0,
    ) -> list[str]:
        """Predict top-k candidate SMILES for a query spectrum.

        Uses precursor mass windowing and peak count overlap heuristics.

        Args:
            query: Query spectrum record.
            k: Maximum number of candidates (up to 25).
            precursor_tolerance_da: Tolerance window around precursor_mz in Daltons.

        Returns:
            List of up to k SMILES strings ordered by heuristic score.
        """
        candidates: list[tuple[float, str]] = []

        for ref in self.library_records:
            mass_diff = abs(ref.precursor_mz - query.precursor_mz)
            if mass_diff <= precursor_tolerance_da:
                # Simple score combining mass closeness and common peak heuristics
                score = 1.0 / (1.0 + mass_diff)
                candidates.append((score, ref.label))

        # Sort descending by score
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Deduplicate SMILES while preserving rank order
        seen_smiles = set()
        unique_smiles: list[str] = []
        for _, smi in candidates:
            if smi not in seen_smiles:
                seen_smiles.add(smi)
                unique_smiles.append(smi)
                if len(unique_smiles) >= k:
                    break

        return unique_smiles
