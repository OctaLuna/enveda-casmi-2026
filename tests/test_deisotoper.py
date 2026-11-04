"""Unit tests for explicit deisotoping algorithm."""

import pytest

from src.data.deisotoper import deisotope_spectrum


def test_deisotope_empty_and_single_peak():
    mzs, ints = deisotope_spectrum([], [])
    assert mzs == []
    assert ints == []

    mzs, ints = deisotope_spectrum([150.0], [1.0])
    assert mzs == [150.0]
    assert ints == [1.0]


def test_deisotope_collapse_plus_one_peak():
    # Peak at 150.0 (intensity 1.0) and +1.0033 Da peak at 151.0033 (intensity 0.15)
    # Plus unrelated peak at 180.0 (intensity 0.5)
    raw_mzs = [150.0, 151.0033, 180.0]
    raw_ints = [1.0, 0.15, 0.5]

    clean_mzs, clean_ints = deisotope_spectrum(
        raw_mzs, raw_ints, mass_tolerance_da=0.015, accumulate_intensity=True
    )

    assert len(clean_mzs) == 2
    assert clean_mzs == [150.0, 180.0]
    assert pytest.approx(clean_ints[0], abs=1e-5) == 1.15
    assert pytest.approx(clean_ints[1], abs=1e-5) == 0.5


def test_deisotope_collapse_plus_two_peak():
    # Monoisotopic peak at 200.0, +1 peak at 201.003, +2 peak at 202.006
    raw_mzs = [200.0, 201.003, 202.006]
    raw_ints = [1.0, 0.20, 0.05]

    clean_mzs, clean_ints = deisotope_spectrum(
        raw_mzs, raw_ints, mass_tolerance_da=0.015, accumulate_intensity=True
    )

    assert len(clean_mzs) == 1
    assert clean_mzs == [200.0]
    assert pytest.approx(clean_ints[0], abs=1e-5) == 1.25


def test_deisotope_does_not_collapse_non_isotope_peaks():
    # Peak at 150.0 and 150.8 (delta 0.8 is not ~1.0033 or ~2.006)
    raw_mzs = [150.0, 150.8, 152.5]
    raw_ints = [1.0, 0.8, 0.4]

    clean_mzs, clean_ints = deisotope_spectrum(
        raw_mzs, raw_ints, mass_tolerance_da=0.015
    )

    assert len(clean_mzs) == 3
    assert clean_mzs == raw_mzs
    assert clean_ints == raw_ints


def test_deisotope_higher_intensity_is_not_collapsed_into_lower():
    # If peak at 151.003 has HIGHER intensity than 150.0, it is likely a distinct fragment,
    # not a 13C isotope of the smaller preceding peak.
    raw_mzs = [150.0, 151.0033]
    raw_ints = [0.05, 1.0]

    clean_mzs, _clean_ints = deisotope_spectrum(
        raw_mzs, raw_ints, mass_tolerance_da=0.015
    )

    assert len(clean_mzs) == 2
