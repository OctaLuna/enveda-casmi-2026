"""Comprehensive natural products benchmark suite for chemical filters, formula estimation and candidate indexing."""

import pytest

from src.data.candidate_db import CandidateDatabase
from src.data.formula_estimator import FormulaEstimator

# Well-characterized natural products (alkaloids, flavonoids, terpenoids, polyphenols)
NATURAL_PRODUCTS = [
    {
        "name": "Caffeine",
        "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C",
        "formula": "C8H10N4O2",
        "mass": 194.080376,
        "class": "Alkaloid",
    },
    {
        "name": "Morphine",
        "smiles": "CN1CCC23C4C1CC5=C2C(=C(C=C5)O)OC3C(C=C4)O",
        "formula": "C17H19NO3",
        "mass": 285.136493,
        "class": "Alkaloid",
    },
    {
        "name": "Nicotine",
        "smiles": "CN1CCCC1c2cccnc2",
        "formula": "C10H14N2",
        "mass": 162.115698,
        "class": "Alkaloid",
    },
    {
        "name": "Quercetin",
        "smiles": "O=c1c(O)c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12",
        "formula": "C15H10O7",
        "mass": 302.042653,
        "class": "Flavonoid",
    },
    {
        "name": "Resveratrol",
        "smiles": "Oc1ccc(/C=C/c2cc(O)cc(O)c2)cc1",
        "formula": "C14H12O3",
        "mass": 228.078644,
        "class": "Polyphenol",
    },
    {
        "name": "Artemisinin",
        "smiles": "CC1CCC2C(C)C(=O)OC3OC4(C)CCC1C23OO4",
        "formula": "C15H22O5",
        "mass": 282.146724,
        "class": "Sesquiterpene Lactone",
    },
]


@pytest.mark.parametrize("np_item", NATURAL_PRODUCTS)
def test_natural_product_chemical_validity(np_item):
    # Parse formula into counts
    from src.data.candidate_db import smiles_to_formula_and_mass

    formula, exact_mass = smiles_to_formula_and_mass(np_item["smiles"])
    assert formula == np_item["formula"]
    assert pytest.approx(exact_mass, abs=1e-4) == np_item["mass"]


@pytest.mark.parametrize("np_item", NATURAL_PRODUCTS)
def test_natural_product_formula_recovery(np_item):
    estimator = FormulaEstimator(ppm_tolerance=5.0)
    candidates = estimator.estimate_formulas(np_item["mass"])

    found_formulas = [c.formula for c in candidates]
    assert np_item["formula"] in found_formulas
    # True formula must be ranked in top 3
    assert np_item["formula"] in found_formulas[:3]


def test_natural_products_in_candidate_database():
    db = CandidateDatabase()
    for item in NATURAL_PRODUCTS:
        db.add_candidate(smiles=item["smiles"], source="LOTUS")

    assert db.size == len(NATURAL_PRODUCTS)

    # Query quercetin
    quercetin_candidates = db.get_candidates("C15H10O7")
    assert len(quercetin_candidates) == 1
    assert "LOTUS" in quercetin_candidates[0].sources

    # Query morphine
    morphine_candidates = db.get_candidates("C17H19NO3")
    assert len(morphine_candidates) == 1
