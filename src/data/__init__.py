"""Data loading, preprocessing, cleaning, and anti-leakage splitting modules for CASMI 2026."""

from src.data.adduct_normalizer import (
    ADDUCT_MAP,
    calculate_neutral_mass,
    normalize_adduct_string,
)
from src.data.deduplicator import (
    cosine_spectral_similarity,
    deduplicate_spectra,
)
from src.data.deisotoper import deisotope_spectrum
from src.data.loader import (
    iter_spectrum_records,
    load_spectrum_records,
    validate_parquet_schema,
)
from src.data.preprocessor import SpectrumPreprocessor
from src.data.spectrum_parser import SpectrumRecord
from src.data.splitter import (
    StructuralSplitter,
    compute_molecular_scaffold,
    generate_and_save_splits,
)

__all__ = [
    "ADDUCT_MAP",
    "SpectrumPreprocessor",
    "SpectrumRecord",
    "StructuralSplitter",
    "calculate_neutral_mass",
    "compute_molecular_scaffold",
    "cosine_spectral_similarity",
    "deduplicate_spectra",
    "deisotope_spectrum",
    "generate_and_save_splits",
    "iter_spectrum_records",
    "load_spectrum_records",
    "normalize_adduct_string",
    "validate_parquet_schema",
]
