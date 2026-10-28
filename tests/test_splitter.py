"""Unit tests for the anti-leakage 3-class structural validation splitter."""

import json

import pytest

from src.data.spectrum_parser import SpectrumMetadata
from src.data.splitter import (
    DEFAULT_SEEDS,
    StructuralSplitter,
    _ExactTanimotoSearch,
    _iter_molecular_feature_jobs,
    _molecular_features,
    compute_mean_nearest_neighbor_tanimoto_distance,
    generate_and_save_splits,
    iter_records_for_split,
)

pytest.importorskip("rdkit")


@pytest.fixture
def mock_spectra():
    molecules = [
        ("mol_phenol", "c1ccccc1O", 3),
        ("mol_pyridine", "c1ccncc1", 2),
        ("mol_cyclohexanol", "C1CCCCC1O", 2),
        ("mol_adamantane", "C1C2CC3CC1CC(C2)C3", 1),
        ("mol_norbornane", "C1CC2CCC1C2", 1),
        ("mol_thf", "C1CCOC1", 1),
        ("mol_naphthalene", "c1ccc2ccccc2c1", 1),
        ("mol_acetic_acid", "CC(=O)O", 1),
        ("mol_ethylamine", "CCN", 1),
        ("mol_decalin", "C1CCC2CCCCC2C1", 1),
        ("mol_quinoline", "c1ccc2ncccc2c1", 1),
        ("mol_oxetane", "C1COC1", 1),
    ]
    return [
        SpectrumMetadata(
            molecule_id=molecule_id,
            spectrum_id=f"{molecule_id}_spectrum_{index}",
            label=smiles,
        )
        for molecule_id, smiles, count in molecules
        for index in range(count)
    ]


def _membership_fields(split):
    return {
        key: value
        for key, value in split.items()
        if key != "metadata"
    }


def test_structural_splitter_disjoint_leakage(mock_spectra):
    split = StructuralSplitter(seed=42).split(iter(mock_spectra))

    train_mols = set(split["train_molecule_ids"])
    val1_mols = set(split["val_clase1_molecule_ids"])
    val2_mols = set(split["val_clase2_molecule_ids"])
    val3_mols = set(split["val_clase3_molecule_ids"])
    excluded_mols = set(split["val_clase3_excluded_neighbor_molecule_ids"])
    val1_queries = set(split["val_clase1_query_spectrum_ids"])

    assert val1_mols <= train_mols
    assert not (val2_mols & train_mols)
    assert not (val3_mols & train_mols)
    assert not (val2_mols & val3_mols)
    assert not (excluded_mols & train_mols)
    assert not (excluded_mols & (val1_mols | val2_mols | val3_mols))

    train_library_spectra = {
        record.spectrum_id
        for record in iter_records_for_split(mock_spectra, split, "train")
    }
    val1_spectra = {
        record.spectrum_id
        for record in iter_records_for_split(mock_spectra, split, "val_clase1")
    }
    assert not (val1_queries & train_library_spectra)
    assert val1_queries == val1_spectra
    assert {
        record.molecule_id
        for record in iter_records_for_split(mock_spectra, split, "val_clase2")
    } == val2_mols
    assert {
        record.molecule_id
        for record in iter_records_for_split(mock_spectra, split, "val_clase3")
    } == val3_mols
    assert (
        split["metadata"]["mean_val_clase3_nearest_train_tanimoto_distance"]
        > 0.60
    )


def test_structural_splitter_generates_all_three_classes(mock_spectra):
    split = StructuralSplitter(seed=42).split(mock_spectra)

    assert split["val_clase1_molecule_ids"]
    assert split["val_clase1_query_spectrum_ids"]
    assert split["val_clase2_molecule_ids"]
    assert split["val_clase3_molecule_ids"]
    assert split["train_molecule_ids"]


def test_structural_splitter_reproducibility(mock_spectra):
    split_one = StructuralSplitter(seed=42).split(iter(mock_spectra))
    split_two = StructuralSplitter(seed=42).split(iter(mock_spectra))

    assert _membership_fields(split_one) == _membership_fields(split_two)
    assert split_one["metadata"]["seed"] == 42
    assert split_two["metadata"]["seed"] == 42


def test_nearest_neighbor_tanimoto_distance_uses_max_similarity():
    from rdkit import DataStructs

    _, phenol_scaffold, phenol_fp = _molecular_features("c1ccccc1O")
    _, _, resorcinol_fp = _molecular_features("Oc1cccc(O)c1")
    _, _, adamantane_fp = _molecular_features("C1C2CC3CC1CC(C2)C3")
    assert phenol_scaffold

    fingerprints = {
        "phenol": phenol_fp,
        "resorcinol": resorcinol_fp,
        "adamantane": adamantane_fp,
    }
    self_distance = compute_mean_nearest_neighbor_tanimoto_distance(
        ["phenol"], ["resorcinol", "adamantane"], fingerprints
    )
    expected_distance = 1.0 - max(
        DataStructs.TanimotoSimilarity(phenol_fp, resorcinol_fp),
        DataStructs.TanimotoSimilarity(phenol_fp, adamantane_fp),
    )
    assert self_distance == pytest.approx(expected_distance)
    assert self_distance < 0.60


def test_exact_tanimoto_search_matches_rdkit_pairwise_values():
    import numpy as np
    from rdkit import DataStructs

    _, _, phenol_fp = _molecular_features("c1ccccc1O")
    _, _, resorcinol_fp = _molecular_features("Oc1cccc(O)c1")
    _, _, adamantane_fp = _molecular_features("C1C2CC3CC1CC(C2)C3")
    references = [resorcinol_fp, adamantane_fp, phenol_fp]

    actual = _ExactTanimotoSearch(references).similarities_for(phenol_fp)
    expected = [
        DataStructs.TanimotoSimilarity(phenol_fp, reference)
        for reference in references
    ]

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)


def test_molecular_features_canonicalize_tautomers():
    imine_tautomer = "CC(C)C(N=C(O)Cc1c[nH]c2ccccc12)C(=O)O"
    amide_tautomer = "CC(C)C(NC(=O)Cc1c[nH]c2ccccc12)C(=O)O"

    first = _molecular_features(imine_tautomer)
    second = _molecular_features(amide_tautomer)

    assert first[0] == second[0]
    assert first[1] == second[1]
    assert first[2] == second[2]


def test_parallel_molecular_features_match_serial_results():
    jobs = [
        ("ethanol", "CCO"),
        ("phenol", "c1ccccc1O"),
        ("adamantane", "C1C2CC3CC1CC(C2)C3"),
    ]

    parallel = list(
        _iter_molecular_feature_jobs(jobs, workers=2, batch_size=2)
    )
    expected = {
        molecule_id: _molecular_features(smiles)
        for molecule_id, smiles in jobs
    }

    assert [molecule_id for molecule_id, _, _, _ in parallel] == [
        molecule_id for molecule_id, _ in jobs
    ]
    for molecule_id, canonical, scaffold, fingerprint in parallel:
        assert (canonical, scaffold, fingerprint) == expected[molecule_id]


def test_generate_and_save_splits_writes_compact_manifests(mock_spectra, tmp_path):
    source_hash = "a" * 64
    paths = generate_and_save_splits(
        records=iter(mock_spectra),
        output_dir=tmp_path / "splits",
        seeds=DEFAULT_SEEDS,
        source_sha256=source_hash,
    )
    repeated_paths = generate_and_save_splits(
        records=iter(mock_spectra),
        output_dir=tmp_path / "repeated_splits",
        seeds=DEFAULT_SEEDS,
        source_sha256=source_hash,
    )

    assert set(paths) == set(DEFAULT_SEEDS)
    assert set(repeated_paths) == set(DEFAULT_SEEDS)
    for seed in DEFAULT_SEEDS:
        file_path = tmp_path / "splits" / f"split_seed_{seed}.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        repeated_data = json.loads(
            repeated_paths[seed].read_text(encoding="utf-8")
        )
        assert file_path.exists()
        assert file_path.stat().st_size < 25 * 1024 * 1024
        assert data["schema_version"] == 1
        assert data["metadata"]["seed"] == seed
        assert data["metadata"]["train_sha256"] == source_hash
        assert _membership_fields(data) == _membership_fields(repeated_data)
        assert data["metadata"]["n_val_clase3_molecules"] == len(
            data["val_clase3_molecule_ids"]
        )
        assert "train_spectrum_ids" not in data
        assert "val_clase2_spectrum_ids" not in data


def test_generate_and_save_splits_requires_project_seeds(tmp_path):
    with pytest.raises(ValueError, match="exactly seeds 42, 1337, and 2026"):
        generate_and_save_splits(
            records=iter(()),
            output_dir=tmp_path,
            seeds=(42, 42),
        )
