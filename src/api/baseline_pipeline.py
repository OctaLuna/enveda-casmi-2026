"""End-to-end baseline orchestrator for CASMI 2026.

Connects spectrum preprocessing, the baseline spectral matcher and the
submission formatter: raw records in, ``{molecule_id: top-25 SMILES}`` out.
"""

import logging
from collections import defaultdict
from collections.abc import Iterable, Sequence

from src.data.preprocessor import SpectrumPreprocessor
from src.data.spectrum_parser import SpectrumRecord
from src.models.baseline_agent import BaselineSpectralMatcher
from src.utils.reproducibility import set_seed

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 25


class BaselinePipeline:
    """Preprocess -> index -> retrieve -> fuse per molecule -> top-25."""

    def __init__(
        self,
        preprocessor: SpectrumPreprocessor | None = None,
        matcher: BaselineSpectralMatcher | None = None,
        precursor_tolerance_da: float = 5.0,
        max_candidates: int = MAX_CANDIDATES,
        seed: int = 42,
    ):
        self.preprocessor = preprocessor or SpectrumPreprocessor()
        self.matcher = matcher or BaselineSpectralMatcher()
        self.precursor_tolerance_da = precursor_tolerance_da
        self.max_candidates = max_candidates
        self.seed = seed

    def fit(self, train_records: Iterable[SpectrumRecord]) -> "BaselinePipeline":
        """Clean the labelled training spectra and index them."""
        set_seed(self.seed)
        cleaned = self.preprocessor.preprocess_batch(train_records, is_test=False)
        self.matcher.fit(cleaned)
        logger.info("Indexed %d training spectra", len(self.matcher.library_records))
        return self

    def predict(self, query_records: Sequence[SpectrumRecord]) -> dict[str, list[str]]:
        """Return up to ``max_candidates`` ranked SMILES for every query molecule.

        Spectra sharing a ``molecule_id`` are fused by summing reciprocal ranks;
        ties break on SMILES so the output is deterministic. Every molecule_id
        present in the input appears in the output (empty list if no hit).
        """
        set_seed(self.seed)
        by_molecule: dict[str, list[SpectrumRecord]] = defaultdict(list)
        for rec in query_records:
            by_molecule[rec.molecule_id].append(rec)

        predictions: dict[str, list[str]] = {}
        for mol_id in sorted(by_molecule):
            scores: dict[str, float] = defaultdict(float)
            for raw in by_molecule[mol_id]:
                query = self.preprocessor.preprocess_record(raw, is_test=True)
                if query is None:
                    continue
                ranked = self.matcher.predict_top_k(
                    query,
                    k=self.max_candidates,
                    precursor_tolerance_da=self.precursor_tolerance_da,
                )
                for rank, smiles in enumerate(ranked, start=1):
                    scores[smiles] += 1.0 / rank
            ordered = sorted(scores, key=lambda s: (-scores[s], s))
            predictions[mol_id] = ordered[: self.max_candidates]
        return predictions
