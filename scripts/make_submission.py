"""Generate submission.csv from train/test parquet files (offline).

Usage:
    python scripts/make_submission.py --train data/raw/train.parquet \
        --test data/raw/test.parquet --output submission.csv
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.submission_pipeline import generate_submission


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/raw/train.parquet")
    parser.add_argument("--test", default="data/raw/test.parquet")
    parser.add_argument("--output", default="submission.csv")
    args = parser.parse_args()
    print(generate_submission(args.train, args.test, args.output))


if __name__ == "__main__":
    main()
