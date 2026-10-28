#!/usr/bin/env python3
"""Generate the three compact CASMI validation split manifests from train.parquet."""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.data.loader import iter_spectrum_metadata
from src.data.splitter import (
    DEFAULT_SEEDS,
    generate_and_save_splits,
)
from src.utils.reproducibility import set_seed


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--train-parquet",
        type=Path,
        default=Path("data/raw/train.parquet"),
        help="Path to the original Kaggle training Parquet.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/splits"),
        help="Directory for the three compact JSON manifests.",
    )
    args = parser.parse_args()

    if not args.train_parquet.is_file():
        parser.error(f"training Parquet not found: {args.train_parquet}")

    set_seed(42)
    source_sha256 = sha256_file(args.train_parquet)
    manifests = generate_and_save_splits(
        records=iter_spectrum_metadata(args.train_parquet),
        output_dir=args.output_dir,
        seeds=DEFAULT_SEEDS,
        source_sha256=source_sha256,
    )

    for seed, manifest in sorted(manifests.items()):
        print(f"seed={seed} file={manifest} bytes={manifest.stat().st_size}")


if __name__ == "__main__":
    main()
