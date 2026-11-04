"""Unit tests for the anti-leakage 3-class structural validation splitter."""

import json

import pytest

from src.data.spectrum_parser import SpectrumRecord
from src.data.splitter import (
    StructuralSplitter,
    generate_and_save_splits,
)


@pytest.fixture
def mock_spectra():
    # 6 molecules:
    # mol_1: 3 spectra (candidate for Val-Clase1)
    # mol_2: 2 spectra (candidate for Val-Clase1)
    # mol_3: 1 spectrum (candidate for Val-Clase2)
    # mol_4: 1 spectrum (candidate for Val-Clase2)
    # mol_5: 1 spectrum (candidate for Val-Clase3, distinct structure)
    # mol_6: 1 spectrum (candidate for Val-Clase3, distinct structure)
    # mol_7, mol_8, mol_9: train spectra
    records = [
        # mol_1 (multi-spec)
        SpectrumRecord(
            "mol_1",
            "spec_1_1",
            [100.0, 150.0],
            [0.5, 1.0],
            200.0,
            "[M+H]+",
            20.0,
            "c1ccccc1O",
        ),
        SpectrumRecord(
            "mol_1",
            "spec_1_2",
            [100.0, 150.0],
            [0.4, 1.0],
            200.0,
            "[M+H]+",
            30.0,
            "c1ccccc1O",
        ),
        SpectrumRecord(
            "mol_1",
            "spec_1_3",
            [100.0, 150.0],
            [0.6, 1.0],
            222.0,
            "[M+Na]+",
            30.0,
            "c1ccccc1O",
        ),
        # mol_2 (multi-spec)
        SpectrumRecord(
            "mol_2",
            "spec_2_1",
            [80.0, 120.0],
            [0.3, 1.0],
            180.0,
            "[M+H]+",
            25.0,
            "c1ccccc1N",
        ),
        SpectrumRecord(
            "mol_2",
            "spec_2_2",
            [80.0, 120.0],
            [0.5, 1.0],
            180.0,
            "[M+H]+",
            35.0,
            "c1ccccc1N",
        ),
        # mol_3
        SpectrumRecord(
            "mol_3",
            "spec_3_1",
            [90.0, 110.0],
            [0.4, 1.0],
            160.0,
            "[M+H]+",
            20.0,
            "CC(=O)Oc1ccccc1C(=O)O",
        ),
        # mol_4
        SpectrumRecord(
            "mol_4",
            "spec_4_1",
            [70.0, 130.0],
            [0.2, 1.0],
            175.0,
            "[M+H]+",
            25.0,
            "CC(=O)NC1=CC=C(O)C=C1",
        ),
        # mol_5 (novel steroid-like / adamantane-like structure)
        SpectrumRecord(
            "mol_5",
            "spec_5_1",
            [135.0, 150.0],
            [0.6, 1.0],
            215.0,
            "[M+H]+",
            40.0,
            "C1C2CC3CC1CC(C2)C3",
        ),
        # mol_6
        SpectrumRecord(
            "mol_6",
            "spec_6_1",
            [140.0, 160.0],
            [0.7, 1.0],
            230.0,
            "[M+H]+",
            40.0,
            "C1CC2CCC1C2",
        ),
        # mol_7, 8, 9 (train core)
        SpectrumRecord(
            "mol_7",
            "spec_7_1",
            [60.0, 100.0],
            [0.5, 1.0],
            150.0,
            "[M+H]+",
            20.0,
            "CCCC",
        ),
        SpectrumRecord(
            "mol_8",
            "spec_8_1",
            [70.0, 110.0],
            [0.5, 1.0],
            170.0,
            "[M+H]+",
            20.0,
            "CCCCCC",
        ),
        SpectrumRecord(
            "mol_9",
            "spec_9_1",
            [80.0, 120.0],
            [0.5, 1.0],
            190.0,
            "[M+H]+",
            20.0,
            "CCCCCCCC",
        ),
    ]
    return records


def test_structural_splitter_disjoint_leakage(mock_spectra):
    splitter = StructuralSplitter(seed=42)
    split = splitter.split(mock_spectra)

    train_mols = set(split["train_molecule_ids"])
    val_clase2_mols = set(split["val_clase2_molecule_ids"])
    val_clase3_mols = set(split["val_clase3_molecule_ids"])

    # Strict assertion: Val-Clase2 and Val-Clase3 molecules MUST NOT be in train_mols
    assert len(val_clase2_mols & train_mols) == 0
    assert len(val_clase3_mols & train_mols) == 0
    assert len(val_clase2_mols & val_clase3_mols) == 0

    # Val-Clase1 query spectra must NOT be in training library
    val_clase1_queries = set(split["val_clase1_query_spectrum_ids"])
    train_spectra = set(split["train_spectrum_ids"])
    assert len(val_clase1_queries & train_spectra) == 0


def test_structural_splitter_generates_all_three_classes(mock_spectra):
    splitter = StructuralSplitter(seed=42)
    split = splitter.split(mock_spectra)

    assert len(split["val_clase1_molecule_ids"]) > 0
    assert len(split["val_clase2_molecule_ids"]) > 0
    assert len(split["val_clase3_molecule_ids"]) > 0
    assert len(split["train_molecule_ids"]) > 0


def test_structural_splitter_reproducibility(mock_spectra):
    # Same seed must produce identical splits
    s1 = StructuralSplitter(seed=42).split(mock_spectra)
    s2 = StructuralSplitter(seed=42).split(mock_spectra)
    assert s1["train_molecule_ids"] == s2["train_molecule_ids"]
    assert s1["val_clase1_molecule_ids"] == s2["val_clase1_molecule_ids"]

    # Different seeds should produce variations
    s3 = StructuralSplitter(seed=1337).split(mock_spectra)
    # The random generator for holdout query spectrum or partition will vary
    assert s1 != s3 or len(mock_spectra) < 5


def test_generate_and_save_splits(mock_spectra, tmp_path):
    seeds = [42, 1337, 2026]
    output_dir = tmp_path / "splits"

    manifest = generate_and_save_splits(
        records=mock_spectra,
        output_dir=output_dir,
        seeds=seeds,
    )

    assert len(manifest) == 3
    for seed in seeds:
        file_path = output_dir / f"split_seed_{seed}.json"
        assert file_path.exists()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "train_molecule_ids" in data
        assert "val_clase1_query_spectrum_ids" in data
        assert "val_clase2_molecule_ids" in data
        assert "val_clase3_molecule_ids" in data
        assert data["metadata"]["seed"] == seed
