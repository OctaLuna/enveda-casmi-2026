"""Parquet -> submission.csv: fit the baseline on train, predict test, validate."""

import logging
from pathlib import Path

from src.api.baseline_pipeline import BaselinePipeline
from src.api.submission import validate_submission_csv, write_submission_csv
from src.data.loader import load_spectrum_records

logger = logging.getLogger(__name__)


def generate_submission(
    train_path: str | Path,
    test_path: str | Path,
    output_path: str | Path = "submission.csv",
    max_train_records: int | None = None,
) -> Path:
    """Build and validate the Kaggle submission using only local artifacts.

    Raises:
        ValueError: if the written file does not cover every test molecule_id
            or violates the format checks of ``validate_submission_csv``.
    """
    train = load_spectrum_records(train_path, max_records=max_train_records)
    test = load_spectrum_records(test_path, is_test=True)
    logger.info("Loaded %d train and %d test spectra", len(train), len(test))

    predictions = BaselinePipeline().fit(train).predict(test)
    out = write_submission_csv(predictions, output_path)
    validate_submission_csv(
        out, expected_molecule_ids=sorted({r.molecule_id for r in test})
    )
    return out
