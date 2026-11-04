"""Unit tests for exact molecular formula estimator."""

from src.data.formula_estimator import (
    FormulaEstimator,
    hill_formula,
)


def test_hill_formula_formatting():
    assert hill_formula({"C": 8, "H": 10, "N": 4, "O": 2}) == "C8H10N4O2"
    assert hill_formula({"C": 2, "H": 6, "O": 1}) == "C2H6O"
    assert hill_formula({"H": 2, "O": 1}) == "H2O"
    assert hill_formula({"C": 1, "H": 4}) == "CH4"
    assert hill_formula({"C": 6, "H": 5, "Cl": 1}) == "C6H5Cl"


def test_estimate_caffeine_formula():
    # Caffeine C8H10N4O2: exact neutral monoisotopic mass = 194.080376
    caffeine_mass = 194.080376
    estimator = FormulaEstimator(ppm_tolerance=5.0)
    candidates = estimator.estimate_formulas(caffeine_mass)

    assert len(candidates) > 0
    top_hit = candidates[0]
    assert top_hit.formula == "C8H10N4O2"
    assert top_hit.counts["C"] == 8
    assert top_hit.counts["H"] == 10
    assert top_hit.counts["N"] == 4
    assert top_hit.counts["O"] == 2
    assert abs(top_hit.ppm_error) < 1.0
    assert top_hit.dbe == 6.0
    assert top_hit.confidence_score > 0.8


def test_estimate_quercetin_formula():
    # Quercetin C15H10O7: exact neutral mass = 302.042653
    quercetin_mass = 302.042653
    estimator = FormulaEstimator(ppm_tolerance=5.0)
    candidates = estimator.estimate_formulas(quercetin_mass)

    assert any(c.formula == "C15H10O7" for c in candidates)
    # The true formula must be among top 3 hits
    formulas = [c.formula for c in candidates[:3]]
    assert "C15H10O7" in formulas


def test_estimate_with_halogens():
    # Chlorobenzene C6H5Cl: M = 112.007978
    chlorobenzene_mass = 112.007978
    estimator = FormulaEstimator(ppm_tolerance=5.0, allow_halogens=True)
    candidates = estimator.estimate_formulas(chlorobenzene_mass)

    assert any(c.formula == "C6H5Cl" for c in candidates)


def test_estimate_invalid_inputs():
    estimator = FormulaEstimator()
    assert estimator.estimate_formulas(0.0) == []
    assert estimator.estimate_formulas(-100.0) == []
    assert estimator.estimate_formulas(200.0, ppm_tolerance=0.0) == []
