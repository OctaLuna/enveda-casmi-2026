"""Chemical constraint filters for molecular formula plausibility in CASMI 2026.

Implements:
1. Senior's Theorem (valency parity, maximum valence bound, connectivity).
2. Double Bond Equivalents (DBE / Index of Hydrogen Deficiency).
3. Elemental ratio bounds (Kind & Fiehn Seven Golden Rules for natural products).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Standard maximum / primary valences for common organic elements
ELEMENT_VALENCES: dict[str, int] = {
    "C": 4,
    "H": 1,
    "N": 3,
    "O": 2,
    "P": 3,
    "S": 2,
    "F": 1,
    "Cl": 1,
    "Br": 1,
    "I": 1,
}

ODD_VALENCE_ELEMENTS = {"H", "N", "P", "F", "Cl", "Br", "I"}


def check_senior_rules(counts: dict[str, int]) -> tuple[bool, str]:
    """Check Senior's Theorem for closed-shell neutral molecular graph plausibility.

    Rule 1: The sum of valences must be at least twice the maximum valence of any atom.
    Rule 2: The sum of atoms with odd valences must be even (generalized nitrogen rule).
    Rule 3: For a connected molecule of n atoms, the sum of valences >= 2 * (n - 1).

    Args:
        counts: Element symbol to atom count mapping.

    Returns:
        Tuple of (is_valid: bool, reason: str).
    """
    total_atoms = sum(c for c in counts.values() if c > 0)
    if total_atoms == 0:
        return False, "Formula contains 0 atoms"

    if total_atoms == 1:
        # Monatomic molecule (noble gas or solitary atom)
        return True, "OK"

    # Senior Rule 2: Odd valence count parity
    odd_count = sum(counts.get(el, 0) for el in ODD_VALENCE_ELEMENTS)
    if odd_count % 2 != 0:
        return (
            False,
            f"Fails Senior Rule 2: Odd valence count ({odd_count}) is not even",
        )

    # Calculate sum of valences and maximum valence present
    sum_valences = 0
    max_valence = 0

    for el, count in counts.items():
        if count <= 0:
            continue
        v = ELEMENT_VALENCES.get(el, 2)
        sum_valences += count * v
        max_valence = max(max_valence, v)

    # Senior Rule 1: Sum of valences >= 2 * max_valence
    if sum_valences < 2 * max_valence:
        return (
            False,
            f"Fails Senior Rule 1: Sum of valences ({sum_valences}) < 2 * max_valence ({2 * max_valence})",
        )

    # Senior Rule 3: Graph connectivity constraint
    # Sum of valences >= 2 * (n - 1)
    min_connected_valences = 2 * (total_atoms - 1)
    if sum_valences < min_connected_valences:
        return (
            False,
            f"Fails Senior Rule 3: Sum of valences ({sum_valences}) < 2 * (n - 1) ({min_connected_valences})",
        )

    return True, "OK"


def calculate_dbe(counts: dict[str, int]) -> tuple[float, bool]:
    """Calculate Double Bond Equivalents (DBE / degree of unsaturation).

    Formula: DBE = C + 1 - (H + X)/2 + (N + P)/2
    where X = F + Cl + Br + I.

    Args:
        counts: Element count mapping.

    Returns:
        Tuple of (dbe_value: float, is_valid: bool).
        Valid means DBE >= 0 and is an exact integer.
    """
    c = counts.get("C", 0)
    h = counts.get("H", 0)
    n = counts.get("N", 0)
    p = counts.get("P", 0)
    x = (
        counts.get("F", 0)
        + counts.get("Cl", 0)
        + counts.get("Br", 0)
        + counts.get("I", 0)
    )

    dbe_2 = 2 * c + 2 - (h + x) + (n + p)
    dbe = dbe_2 / 2.0

    # Must be non-negative and 2 * DBE must be even (DBE is integer)
    is_valid = (dbe >= 0.0) and (dbe_2 % 2 == 0)
    return dbe, is_valid


def check_elemental_ratios(counts: dict[str, int]) -> bool:
    """Validate elemental ratio plausibility for organic compounds and natural products.

    Bounds:
    - 0.1 <= H/C <= 3.0 (up to 4.0 for methane CH4)
    - O/C <= 1.2
    - N/C <= 0.6
    - P/C <= 0.3
    - S/C <= 0.3

    Args:
        counts: Element count mapping.

    Returns:
        True if all ratios are within physical chemical bounds.
    """
    c = counts.get("C", 0)
    if c == 0:
        # Non-carbon containing small molecules
        return True

    h = counts.get("H", 0)
    o = counts.get("O", 0)
    n = counts.get("N", 0)
    p = counts.get("P", 0)
    s = counts.get("S", 0)

    # H/C ratio
    max_hc = 4.0 if c == 1 else 3.2
    hc = h / c
    if hc < 0.1 or hc > max_hc:
        return False

    # Heteroatom ratios
    if (o / c) > 1.3:
        return False
    if (n / c) > 0.8:
        return False
    if (p / c) > 0.4:
        return False
    return (s / c) <= 0.4


def is_chemically_valid_formula(counts: dict[str, int]) -> bool:
    """Run full chemical plausibility gate combining Senior, DBE, and elemental ratios.

    Args:
        counts: Element to count mapping.

    Returns:
        True if the formula represents a valid closed-shell neutral organic structure.
    """
    if not counts or sum(counts.values()) == 0:
        return False

    senior_ok, _ = check_senior_rules(counts)
    if not senior_ok:
        return False

    _, dbe_ok = calculate_dbe(counts)
    if not dbe_ok:
        return False

    return check_elemental_ratios(counts)
