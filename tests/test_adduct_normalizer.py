"""Unit tests for adduct normalization and exact neutral mass calculation."""

import pytest

from src.data.adduct_normalizer import (
    ADDUCT_MAP,
    calculate_neutral_mass,
    normalize_adduct_string,
)


def test_normalize_adduct_string():
    assert normalize_adduct_string("[M + H]+") == "[M+H]+"
    assert normalize_adduct_string(" [M-H]- ") == "[M-H]-"
    assert normalize_adduct_string("[M+2H]2+") == "[M+2H]2+"
    assert normalize_adduct_string("") == ""


def test_calculate_neutral_mass_positive_adducts():
    # Caffeine C8H10N4O2: neutral mass M = 194.080376
    # [M+H]+: mz = M + 1.007276 = 195.087652
    m_calc = calculate_neutral_mass(195.087652, "[M+H]+")
    assert m_calc is not None
    assert pytest.approx(m_calc, abs=1e-4) == 194.080376

    # [M+Na]+: mz = M + 22.989221 = 217.069597
    m_na = calculate_neutral_mass(217.069597, "[M+Na]+")
    assert m_na is not None
    assert pytest.approx(m_na, abs=1e-4) == 194.080376

    # [M+2H]2+: mz = (M + 2 * 1.007276) / 2 = 98.047464
    m_2h = calculate_neutral_mass(98.047464, "[M+2H]2+")
    assert m_2h is not None
    assert pytest.approx(m_2h, abs=1e-4) == 194.080376

    # [2M+H]+: mz = (2 * M + 1.007276) / 1 = 389.168028
    m_dimer = calculate_neutral_mass(389.168028, "[2M+H]+")
    assert m_dimer is not None
    assert pytest.approx(m_dimer, abs=1e-4) == 194.080376


def test_calculate_neutral_mass_negative_adducts():
    # Acetic acid C2H4O2: M = 60.021129
    # [M-H]-: mz = M - 1.007276 = 59.013853
    m_deprot = calculate_neutral_mass(59.013853, "[M-H]-")
    assert m_deprot is not None
    assert pytest.approx(m_deprot, abs=1e-4) == 60.021129

    # [M+FA-H]-: Formate adduct [M + HCOO]-
    # delta = (2*H + C + 2*O) - PROTON = 44.998203 Da
    # mz = 60.021129 + 44.998203 = 105.019332
    m_fa = calculate_neutral_mass(105.019332, "[M+FA-H]-")
    assert m_fa is not None
    assert pytest.approx(m_fa, abs=1e-4) == 60.021129


def test_calculate_neutral_mass_unknown_adduct_returns_none():
    assert calculate_neutral_mass(200.0, "UNKNOWN_ADDUCT") is None
    assert calculate_neutral_mass(200.0, "") is None


def test_all_adducts_in_map():
    expected_adducts = {
        "[M+H]+",
        "[M+Na]+",
        "[M+K]+",
        "[M+NH4]+",
        "[M+H-H2O]+",
        "[M+2H]2+",
        "[2M+H]+",
        "[M-H]-",
        "[M-H-H2O]-",
        "[M+Cl]-",
        "[M+FA-H]-",
    }
    for adduct in expected_adducts:
        assert adduct in ADDUCT_MAP
        res = calculate_neutral_mass(300.0, adduct)
        assert res is not None
        assert res > 0
