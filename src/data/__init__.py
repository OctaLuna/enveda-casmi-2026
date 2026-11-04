"""Data loading, preprocessing, cleaning, chemical filtering, and candidate database modules for CASMI 2026."""

from src.data.adduct_normalizer import (
    ADDUCT_MAP,
    calculate_neutral_mass,
    normalize_adduct_string,
)
from src.data.candidate_db import (
    CandidateDatabase,
    CandidateRecord,
    smiles_to_formula_and_mass,
)
from src.data.chemical_filters import (
    calculate_dbe,
    check_elemental_ratios,
    check_senior_rules,
    is_chemically_valid_formula,
)
from src.data.deduplicator import (
    cosine_spectral_similarity,
    deduplicate_spectra,
)
from src.data.deisotoper import deisotope_spectrum
from src.data.formula_estimator import (
    CandidateFormula,
    FormulaEstimator,
    hill_formula,
)
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
    "CandidateDatabase",
    "CandidateFormula",
    "CandidateRecord",
    "FormulaEstimator",
    "SpectrumPreprocessor",
    "SpectrumRecord",
    "StructuralSplitter",
    "calculate_dbe",
    "calculate_neutral_mass",
    "check_elemental_ratios",
    "check_senior_rules",
    "compute_molecular_scaffold",
    "cosine_spectral_similarity",
    "deduplicate_spectra",
    "deisotope_spectrum",
    "generate_and_save_splits",
    "hill_formula",
    "is_chemically_valid_formula",
    "iter_spectrum_records",
    "load_spectrum_records",
    "normalize_adduct_string",
    "smiles_to_formula_and_mass",
    "validate_parquet_schema",
]
