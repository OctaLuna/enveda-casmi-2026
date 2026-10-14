"""Unit tests for reproducibility and seed locking."""

import random

import numpy as np
import pytest

from src.utils.reproducibility import set_seed


def test_set_seed_determinism():
    """Verify that calling set_seed produces identical random sequences."""
    set_seed(42)
    val1_py = random.random()
    val1_np = np.random.rand()

    set_seed(42)
    val2_py = random.random()
    val2_np = np.random.rand()

    assert val1_py == val2_py
    assert val1_np == val2_np


def test_set_seed_torch_determinism():
    """Verify PyTorch determinism when torch is installed."""
    try:
        import torch

        set_seed(1337)
        t1 = torch.rand(5)

        set_seed(1337)
        t2 = torch.rand(5)

        assert torch.equal(t1, t2)
    except ImportError:
        pytest.skip("PyTorch not installed in test environment")


def test_set_seed_different_seeds_produce_different_values():
    """Verify that different seeds produce distinct outputs."""
    set_seed(42)
    val_a = random.random()

    set_seed(999)
    val_b = random.random()

    assert val_a != val_b
