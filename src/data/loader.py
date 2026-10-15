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

from src.data.spectrum_parser import SpectrumRecord

logger = logging.getLogger(__name__)

COMMON_REQUIRED_COLUMNS = [
    "molecule_id",
    "spectrum_id",
    "ms2_mzs",
    "ms2_normalized_intensities",
    "precursor_mz",
    "adduct",
    "collision_energy_ev",
]

TRAIN_REQUIRED_COLUMNS = COMMON_REQUIRED_COLUMNS + ["label"]
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

    expected = COMMON_REQUIRED_COLUMNS if is_test else TRAIN_REQUIRED_COLUMNS
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
    cols = columns or (COMMON_REQUIRED_COLUMNS if is_test else TRAIN_REQUIRED_COLUMNS)

    for batch in parquet_file.iter_batches(batch_size=batch_size, columns=cols):
        pydict: dict[str, list[Any]] = batch.to_pydict()
        num_rows = len(pydict["molecule_id"])

        for i in range(num_rows):
            label = pydict["label"][i] if "label" in pydict else None
            # Handle possible PyArrow scalar conversion or None
            if label is not None and not isinstance(label, str):
                label = str(label)

            yield SpectrumRecord(
                molecule_id=str(pydict["molecule_id"][i]),
                spectrum_id=str(pydict["spectrum_id"][i]),
                ms2_mzs=[float(x) for x in pydict["ms2_mzs"][i]],
                ms2_normalized_intensities=[
                    float(x) for x in pydict["ms2_normalized_intensities"][i]
                ],
                precursor_mz=float(pydict["precursor_mz"][i]),
                adduct=str(pydict["adduct"][i]),
                collision_energy_ev=float(pydict["collision_energy_ev"][i]),
                label=label,
            )


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
