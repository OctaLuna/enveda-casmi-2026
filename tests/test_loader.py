"""Unit tests for efficient Parquet dataset loader with PyArrow and Polars."""

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.data.loader import (
    iter_spectrum_metadata,
    iter_spectrum_records,
    load_spectrum_records,
    validate_parquet_schema,
)


@pytest.fixture
def sample_parquet_train(tmp_path):
    table = pa.Table.from_arrays(
        [
            pa.array(["mol_1", "mol_2"]),
            pa.array(["spec_1", "spec_2"]),
            pa.array([[100.0, 150.0], [200.0, 250.0, 300.0]]),
            pa.array([[0.2, 1.0], [0.1, 0.5, 1.0]]),
            pa.array([160.0, 310.0]),
            pa.array(["[M+H]+", "[M+Na]+"]),
            pa.array([30.0, 40.0]),
            pa.array(["CCO", "c1ccccc1"]),
        ],
        names=[
            "molecule_id",
            "spectrum_id",
            "ms2_mzs",
            "ms2_normalized_intensities",
            "precursor_mz",
            "adduct",
            "collision_energy_ev",
            "label",
        ],
    )
    file_path = tmp_path / "train_sample.parquet"
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def sample_parquet_test(tmp_path):
    table = pa.Table.from_arrays(
        [
            pa.array(["mol_test_1"]),
            pa.array(["spec_test_1"]),
            pa.array([[80.0, 120.0]]),
            pa.array([[0.5, 1.0]]),
            pa.array([130.0]),
            pa.array(["[M+H]+"]),
            pa.array([25.0]),
        ],
        names=[
            "molecule_id",
            "spectrum_id",
            "ms2_mzs",
            "ms2_normalized_intensities",
            "precursor_mz",
            "adduct",
            "collision_energy_ev",
        ],
    )
    file_path = tmp_path / "test_sample.parquet"
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def sample_kaggle_train(tmp_path):
    table = pa.Table.from_arrays(
        [
            pa.array(["AAALVYBICLMAMA", "AAALVYBICLMAMA"]),
            pa.array(
                [
                    "O=C1NC(=O)c2cc(Nc3ccccc3)c(Nc3ccccc3)cc21",
                    "O=C1NC(=O)c2cc(Nc3ccccc3)c(Nc3ccccc3)cc21",
                ]
            ),
            pa.array([[100.0, 150.0], [110.0, 160.0]]),
            pa.array([[0.2, 1.0], [0.3, 1.0]]),
            pa.array([160.0, 170.0]),
            pa.array(["[M+H]+", "[M+H]+"]),
            pa.array([30.0, 40.0]),
        ],
        names=[
            "inchikey14",
            "normalized_smiles",
            "ms2_mzs",
            "ms2_normalized_intensities",
            "precursor_mz",
            "adduct",
            "collision_energy_ev",
        ],
    )
    file_path = tmp_path / "kaggle_train_sample.parquet"
    pq.write_table(table, file_path)
    return file_path


def test_validate_parquet_schema_success(sample_parquet_train):
    assert validate_parquet_schema(sample_parquet_train, is_test=False) is True


def test_validate_parquet_schema_kaggle_train(sample_kaggle_train):
    assert validate_parquet_schema(sample_kaggle_train, is_test=False) is True


def test_validate_parquet_schema_missing_column(tmp_path):
    table = pa.Table.from_arrays(
        [pa.array(["mol_1"]), pa.array(["spec_1"])],
        names=["molecule_id", "spectrum_id"],
    )
    file_path = tmp_path / "bad.parquet"
    pq.write_table(table, file_path)

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_parquet_schema(file_path, is_test=False)


def test_iter_spectrum_records_train(sample_parquet_train):
    records = list(iter_spectrum_records(sample_parquet_train, batch_size=1))
    assert len(records) == 2

    assert records[0].molecule_id == "mol_1"
    assert records[0].spectrum_id == "spec_1"
    assert records[0].ms2_mzs == [100.0, 150.0]
    assert records[0].ms2_normalized_intensities == [0.2, 1.0]
    assert records[0].precursor_mz == 160.0
    assert records[0].adduct == "[M+H]+"
    assert records[0].collision_energy_ev == 30.0
    assert records[0].label == "CCO"

    assert records[1].molecule_id == "mol_2"
    assert records[1].label == "c1ccccc1"


def test_iter_spectrum_metadata_reads_only_split_columns(sample_parquet_train):
    records = list(iter_spectrum_metadata(sample_parquet_train, batch_size=1))

    observed = [
        (record.molecule_id, record.spectrum_id, record.label) for record in records
    ]
    assert observed == [
        ("mol_1", "spec_1", "CCO"),
        ("mol_2", "spec_2", "c1ccccc1"),
    ]
    assert not hasattr(records[0], "ms2_mzs")


def test_iter_spectrum_metadata_maps_kaggle_train_columns(sample_kaggle_train):
    records = list(iter_spectrum_metadata(sample_kaggle_train, batch_size=1))

    assert [
        (record.molecule_id, record.spectrum_id, record.label) for record in records
    ] == [
        (
            "AAALVYBICLMAMA",
            "train_row_0000000000",
            "O=C1NC(=O)c2cc(Nc3ccccc3)c(Nc3ccccc3)cc21",
        ),
        (
            "AAALVYBICLMAMA",
            "train_row_0000000001",
            "O=C1NC(=O)c2cc(Nc3ccccc3)c(Nc3ccccc3)cc21",
        ),
    ]


def test_iter_spectrum_records_maps_kaggle_train_columns(sample_kaggle_train):
    records = list(iter_spectrum_records(sample_kaggle_train, batch_size=1))

    assert [record.molecule_id for record in records] == [
        "AAALVYBICLMAMA",
        "AAALVYBICLMAMA",
    ]
    assert [record.spectrum_id for record in records] == [
        "train_row_0000000000",
        "train_row_0000000001",
    ]
    assert records[0].label == (
        "O=C1NC(=O)c2cc(Nc3ccccc3)c(Nc3ccccc3)cc21"
    )


def test_iter_spectrum_records_test_no_label(sample_parquet_test):
    records = list(iter_spectrum_records(sample_parquet_test, is_test=True))
    assert len(records) == 1
    assert records[0].molecule_id == "mol_test_1"
    assert records[0].label is None


def test_load_spectrum_records_all(sample_parquet_train):
    records = load_spectrum_records(sample_parquet_train)
    assert len(records) == 2
    assert all(hasattr(r, "peak_count") for r in records)
