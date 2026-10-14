"""Unit tests for MRR@25 calculation and InChIKey14 canonicalization."""

import pytest

from src.utils.metrics import calculate_mrr_at_25, smiles_to_inchikey14


def test_smiles_to_inchikey14_valid():
    key = smiles_to_inchikey14("CCO")
    assert key is not None
    assert len(key) == 14


def test_smiles_to_inchikey14_empty_or_invalid():
    assert smiles_to_inchikey14("") is None
    assert smiles_to_inchikey14(None) is None


def test_calculate_mrr_at_25_perfect_rank_1():
    ground_truth = ["CCO", "c1ccccc1"]
    predictions = [
        ["CCO", "CCC", "CCN"],
        ["c1ccccc1", "c1ccncc1"],
    ]
    # Both at rank 1 -> 1.0 + 1.0 / 2 = 1.0
    score = calculate_mrr_at_25(ground_truth, predictions)
    assert pytest.approx(score, 0.001) == 1.0


def test_calculate_mrr_at_25_rank_2_and_rank_4():
    ground_truth = ["CCO", "c1ccccc1"]
    predictions = [
        ["CCC", "CCO", "CCN"],  # matched at rank 2 -> 0.5
        ["C", "CC", "CCC", "c1ccccc1", "CCCC"],  # matched at rank 4 -> 0.25
    ]
    # Mean = (0.5 + 0.25) / 2 = 0.375
    score = calculate_mrr_at_25(ground_truth, predictions)
    assert pytest.approx(score, 0.001) == 0.375


def test_calculate_mrr_at_25_outside_top_25():
    ground_truth = ["CCO"]
    # 25 wrong molecules, then CCO at position 26
    wrong_candidates = [f"C{i}" for i in range(25)]
    predictions = [wrong_candidates + ["CCO"]]
    score = calculate_mrr_at_25(ground_truth, predictions)
    assert score == 0.0


def test_calculate_mrr_at_25_empty():
    assert calculate_mrr_at_25([], []) == 0.0
