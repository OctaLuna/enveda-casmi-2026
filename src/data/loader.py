"""High-performance Parquet dataset loader for CASMI 2026 LC-MS/MS spectra.

Leverages PyArrow and Polars for memory-efficient batch streaming and schema validation
over large multi-million row datasets (train.parquet / test.parquet).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from src.data.spectrum_parser import SpectrumMetadata, SpectrumRecord

logger = logging.getLogger(__name__)

SPECTRUM_REQUIRED_COLUMNS = [
    "ms2_mzs",
    "ms2_normalized_intensities",
    "precursor_mz",
    "adduct",
    "collision_energy_ev",
]

COMMON_REQUIRED_COLUMNS = [
    "molecule_id",
    "spectrum_id",
    *SPECTRUM_REQUIRED_COLUMNS,
]

TRAIN_REQUIRED_COLUMNS = COMMON_REQUIRED_COLUMNS + ["label"]
KAGGLE_TRAIN_REQUIRED_COLUMNS = [
    "inchikey14",
    "normalized_smiles",
    *SPECTRUM_REQUIRED_COLUMNS,
]
REQUIRED_COLUMNS = TRAIN_REQUIRED_COLUMNS


def validate_parquet_schema(parquet_path: str | Path, is_test: bool = False) -> bool:
    """Validate that the Parquet file contains all expected columns and proper schema.

    Args:
        parquet_path: Path to the .parquet file.
        is_test: True if validating test.parquet (where 'label' is optional/absent).

    Returns:
        True if valid; raises ValueError if required columns are missing.
    """
    path = Path(parquet_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found at: {path}")

    parquet_file = pq.ParquetFile(path)
    schema_names = set(parquet_file.schema_arrow.names)

    if is_test:
        expected = COMMON_REQUIRED_COLUMNS
    elif set(TRAIN_REQUIRED_COLUMNS) <= schema_names:
        expected = TRAIN_REQUIRED_COLUMNS
    elif set(KAGGLE_TRAIN_REQUIRED_COLUMNS) <= schema_names:
        expected = KAGGLE_TRAIN_REQUIRED_COLUMNS
    else:
        expected = KAGGLE_TRAIN_REQUIRED_COLUMNS
    missing = set(expected) - schema_names

    if missing:
        raise ValueError(
            f"Missing required columns in {path.name}: {sorted(missing)}. "
            f"Available columns: {sorted(schema_names)}"
        )

    return True


def iter_spectrum_records(
    parquet_path: str | Path,
    batch_size: int = 10_000,
    is_test: bool = False,
    columns: list[str] | None = None,
) -> Iterator[SpectrumRecord]:
    """Stream SpectrumRecord objects in memory-safe batches from a Parquet file.

    Args:
        parquet_path: Path to train.parquet or test.parquet.
        batch_size: Number of rows per PyArrow RecordBatch.
        is_test: True if loading test set without labels.
        columns: Specific columns to load (must include required columns).

    Yields:
        SpectrumRecord instances validated against length constraints.
    """
    validate_parquet_schema(parquet_path, is_test=is_test)

    parquet_file = pq.ParquetFile(parquet_path)
    schema_names = set(parquet_file.schema_arrow.names)
    if is_test:
        molecule_column = "molecule_id"
        spectrum_column = "spectrum_id"
        label_column = None
    elif set(TRAIN_REQUIRED_COLUMNS) <= schema_names:
        molecule_column = "molecule_id"
        spectrum_column = "spectrum_id"
        label_column = "label"
    else:
        molecule_column = "inchikey14"
        spectrum_column = "spectrum_id" if "spectrum_id" in schema_names else None
        label_column = "normalized_smiles"

    default_columns = [molecule_column, *SPECTRUM_REQUIRED_COLUMNS]
    if spectrum_column is not None:
        default_columns.append(spectrum_column)
    if label_column is not None:
        default_columns.append(label_column)
    cols = columns or default_columns
    missing_columns = set(cols) - schema_names
    if missing_columns:
        raise ValueError(
            f"Requested columns are missing from {Path(parquet_path).name}: "
            f"{sorted(missing_columns)}"
        )
    required_columns = {molecule_column, *SPECTRUM_REQUIRED_COLUMNS}
    if spectrum_column is not None:
        required_columns.add(spectrum_column)
    if label_column is not None:
        required_columns.add(label_column)
    if not required_columns <= set(cols):
        raise ValueError(
            f"columns must include required fields: {sorted(required_columns)}"
        )

    row_offset = 0
    for batch in parquet_file.iter_batches(batch_size=batch_size, columns=cols):
        pydict: dict[str, list[Any]] = batch.to_pydict()
        num_rows = len(pydict[molecule_column])

        for i in range(num_rows):
            label = pydict[label_column][i] if label_column is not None else None
            # Handle possible PyArrow scalar conversion or None
            if label is not None and not isinstance(label, str):
                label = str(label)

            yield SpectrumRecord(
                molecule_id=str(pydict[molecule_column][i]),
                spectrum_id=(
                    str(pydict[spectrum_column][i])
                    if spectrum_column is not None
                    else f"train_row_{row_offset + i:010d}"
                ),
                ms2_mzs=[float(x) for x in pydict["ms2_mzs"][i]],
                ms2_normalized_intensities=[
                    float(x) for x in pydict["ms2_normalized_intensities"][i]
                ],
                precursor_mz=float(pydict["precursor_mz"][i]),
                adduct=str(pydict["adduct"][i]),
                collision_energy_ev=float(pydict["collision_energy_ev"][i]),
                label=label,
            )
        row_offset += num_rows


def iter_spectrum_metadata(
    parquet_path: str | Path,
    batch_size: int = 100_000,
) -> Iterator[SpectrumMetadata]:
    """Stream only the columns needed for structural split generation."""
    validate_parquet_schema(parquet_path)
    parquet_file = pq.ParquetFile(parquet_path)
    schema_names = set(parquet_file.schema_arrow.names)
    molecule_column = "molecule_id" if "molecule_id" in schema_names else "inchikey14"
    spectrum_column = "spectrum_id" if "spectrum_id" in schema_names else None
    label_column = "label" if "label" in schema_names else "normalized_smiles"
    metadata_columns = [molecule_column, label_column]
    if spectrum_column is not None:
        metadata_columns.append(spectrum_column)

    row_offset = 0
    for batch in parquet_file.iter_batches(
        batch_size=batch_size, columns=metadata_columns
    ):
        columns: dict[str, list[Any]] = batch.to_pydict()
        molecules = columns[molecule_column]
        labels = columns[label_column]
        spectra = columns[spectrum_column] if spectrum_column is not None else None
        for index, (molecule_id, label) in enumerate(zip(molecules, labels)):
            spectrum_id = spectra[index] if spectra is not None else None
            if (
                molecule_id is None
                or label is None
                or (spectrum_column is not None and spectrum_id is None)
            ):
                raise ValueError(
                    "Split metadata contains a null molecule, spectrum, or label"
                )
            if spectrum_id is None:
                spectrum_id = f"train_row_{row_offset + index:010d}"
            yield SpectrumMetadata(
                molecule_id=str(molecule_id),
                spectrum_id=str(spectrum_id),
                label=str(label),
            )
        row_offset += len(molecules)


def load_spectrum_records(
    parquet_path: str | Path,
    max_records: int | None = None,
    is_test: bool = False,
) -> list[SpectrumRecord]:
    """Load spectrum records into a Python list up to max_records.

    Args:
        parquet_path: Path to the Parquet dataset.
        max_records: Optional cap on the number of records to load.
        is_test: Set to True when loading test set without labels.

    Returns:
        List of SpectrumRecord objects.
    """
    records: list[SpectrumRecord] = []
    for rec in iter_spectrum_records(parquet_path, is_test=is_test):
        records.append(rec)
        if max_records is not None and len(records) >= max_records:
            break
    return records
