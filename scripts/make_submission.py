"""Generate submission.csv from train/test parquet files (offline).

Usage:
    python scripts/make_submission.py --train data/raw/train.parquet \
        --test data/raw/test.parquet --output submission.csv
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.submission_pipeline import generate_submission


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/raw/train.parquet")
    parser.add_argument("--test", default="data/raw/test.parquet")
    parser.add_argument("--output", default="submission.csv")
    parser.add_argument(
        "--split-manifest",
        default=None,
        help="Indexa solo las moleculas train_molecule_ids de este manifiesto.",
    )
    args = parser.parse_args()
    library = None
    if args.split_manifest:
        with open(args.split_manifest, encoding="utf-8") as f:
            library = set(json.load(f)["train_molecule_ids"])
    print(
        generate_submission(
            args.train, args.test, args.output, library_molecule_ids=library
        )
    )


if __name__ == "__main__":
    main()
