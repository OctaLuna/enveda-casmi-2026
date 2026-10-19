"""Unit tests for chemical constraints: Senior rules, DBE, and elemental ratios."""

from src.data.chemical_filters import (
    calculate_dbe,
    check_elemental_ratios,
    check_senior_rules,
    is_chemically_valid_formula,
)


def test_dbe_calculation_valid_molecules():
    # Methane: CH4 -> DBE = 1 + 1 - 4/2 = 0
    dbe, valid = calculate_dbe({"C": 1, "H": 4})
    assert valid is True
    assert dbe == 0.0

    # Benzene: C6H6 -> DBE = 6 + 1 - 6/2 = 4
    dbe, valid = calculate_dbe({"C": 6, "H": 6})
    assert valid is True
    assert dbe == 4.0

    # Caffeine: C8H10N4O2 -> DBE = 8 + 1 - 10/2 + 4/2 = 6
    dbe, valid = calculate_dbe({"C": 8, "H": 10, "N": 4, "O": 2})
    assert valid is True
    assert dbe == 6.0

    # Chloroethane: C2H5Cl -> DBE = 2 + 1 - (5+1)/2 = 0
    dbe, valid = calculate_dbe({"C": 2, "H": 5, "Cl": 1})
    assert valid is True
    assert dbe == 0.0


def test_dbe_calculation_invalid_molecules():
    # Impossible hyper-hydrogenated: CH5 -> DBE = 1 + 1 - 5/2 = -0.5
    dbe, valid = calculate_dbe({"C": 1, "H": 5})
    assert valid is False
    assert dbe < 0 or dbe % 1 != 0

    # C2H7 -> DBE = 2 + 1 - 7/2 = -0.5
    dbe, valid = calculate_dbe({"C": 2, "H": 7})
    assert valid is False


def test_senior_rules_valid_molecules():
    # Water: H2O (C=0, H=2, O=1)
    # v: H=1, O=2. sum=4. max=2. sum >= 2*2 (4>=4). odd: H=2 (even). n=3: sum >= 2*(3-1)=4 (4>=4)
    valid, reason = check_senior_rules({"H": 2, "O": 1})
    assert valid is True
    assert reason == "OK"

    # Ethanol: C2H6O
    valid, reason = check_senior_rules({"C": 2, "H": 6, "O": 1})
    assert valid is True

    # Caffeine: C8H10N4O2
    valid, reason = check_senior_rules({"C": 8, "H": 10, "N": 4, "O": 2})
    assert valid is True


def test_senior_rules_odd_valences_fails():
    # Methyl radical: CH3 (3 hydrogens with odd valence 1 -> odd count 3 -> fails rule 2)
    valid, reason = check_senior_rules({"C": 1, "H": 3})
    assert valid is False
    assert "odd" in reason.lower() or "paridad" in reason.lower()


def test_senior_rules_isolated_atoms_fails():
    # C1 H10: n=11, sum valences = 4 + 10 = 14. But 2*(11-1) = 20 > 14 (fails rule 3)
    valid, _reason = check_senior_rules({"C": 1, "H": 10})
    assert valid is False


def test_elemental_ratios():
    # Plausible natural product: Quercetin C15H10O7 -> H/C = 0.67, O/C = 0.47
    assert check_elemental_ratios({"C": 15, "H": 10, "O": 7}) is True

    # Impossible: C10 H60 (H/C = 6.0 > 3.0)
    assert check_elemental_ratios({"C": 10, "H": 60}) is False

    # Impossible: C2 O10 (O/C = 5.0 > 1.2)
    assert check_elemental_ratios({"C": 2, "O": 10}) is False


def test_is_chemically_valid_formula():
    # Valid natural products
    assert (
        is_chemically_valid_formula({"C": 8, "H": 10, "N": 4, "O": 2}) is True
    )  # Caffeine
    assert is_chemically_valid_formula({"C": 9, "H": 8, "O": 4}) is True  # Aspirin

    # Invalid formulas
    assert is_chemically_valid_formula({"C": 1, "H": 5}) is False  # CH5
    assert is_chemically_valid_formula({"C": 1, "H": 3}) is False  # CH3 radical
    assert is_chemically_valid_formula({}) is False  # Empty
