"""Baseline candidate retrieval model for CASMI 2026.

Provides spectral retrieval and heuristic baseline matching interfaces.
"""

from collections.abc import Sequence
from bisect import bisect_left, bisect_right
from src.data.spectrum_parser import SpectrumRecord
from src.models.interfaces import CandidatePrediction
from src.models.retrieval.spectral_similarity import (
    cosine_similarity,
    cosine_entropy_similarities,
)


class BaselineSpectralMatcher:
    """Baseline retrieval engine matching query spectra against a known training library."""

    def __init__(
        self,
        strategy: str = "cosine",
        cosine_weight: float = 0.5,
        entropy_weight: float = 0.5,
        fragment_tolerance_da: float = 0.02,
    ):
        if strategy not in {"cosine", "weighted_fusion"}:
            raise ValueError("strategy must be 'cosine' or 'weighted_fusion'")
        if (
            cosine_weight < 0
            or entropy_weight < 0
            or abs(cosine_weight + entropy_weight - 1) > 1e-9
        ):
            raise ValueError(
                "cosine_weight and entropy_weight must be non-negative and sum to 1"
            )
        self.strategy = strategy
        self.cosine_weight = cosine_weight
        self.entropy_weight = entropy_weight
        self.fragment_tolerance_da = fragment_tolerance_da
        self.library_records: list[SpectrumRecord] = []
        self._precursor_masses: list[float] = []
        self._sorted_library: list[SpectrumRecord] = []

    def fit(self, records: Sequence[SpectrumRecord]) -> "BaselineSpectralMatcher":
        """Index training spectrum records with valid ground-truth SMILES labels."""
        self.library_records = [rec for rec in records if rec.label]
        self._sorted_library = sorted(
            self.library_records, key=lambda rec: rec.precursor_mz
        )
        self._precursor_masses = [rec.precursor_mz for rec in self._sorted_library]
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
        return [
            item.smiles
            for item in self.predict_candidates(query, k, precursor_tolerance_da)
        ]

    def predict_candidates(
        self, query: SpectrumRecord, k: int = 25, precursor_tolerance_da: float = 5.0
    ) -> list[CandidatePrediction]:
        if k <= 0:
            return []
        candidates: dict[str, tuple[float, float]] = {}

        lower = bisect_left(
            self._precursor_masses, query.precursor_mz - precursor_tolerance_da
        )
        upper = bisect_right(
            self._precursor_masses, query.precursor_mz + precursor_tolerance_da
        )
        for ref in self._sorted_library[lower:upper]:
            mass_diff = abs(ref.precursor_mz - query.precursor_mz)
            if mass_diff <= precursor_tolerance_da:
                if self.strategy == "cosine":
                    cosine = cosine_similarity(query, ref, self.fragment_tolerance_da)
                    score = cosine
                else:
                    cosine, entropy = cosine_entropy_similarities(
                        query, ref, self.fragment_tolerance_da
                    )
                    score = self.cosine_weight * cosine + self.entropy_weight * entropy
                previous = candidates.get(ref.label)
                if (
                    previous is None
                    or score > previous[0]
                    or (score == previous[0] and mass_diff < previous[1])
                ):
                    candidates[ref.label] = (score, mass_diff)
        ordered = sorted(
            candidates.items(), key=lambda item: (-item[1][0], item[1][1], item[0])
        )[:k]
        return [
            CandidatePrediction(smiles, float(score_and_mass[0]), rank)
            for rank, (smiles, score_and_mass) in enumerate(ordered, 1)
        ]
