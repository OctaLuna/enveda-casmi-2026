"""Benchmark the baseline on Val-Clase1/2/3 and export a markdown report.

Usage:
    python scripts/evaluate_baseline.py --train data/raw/train.parquet \
        --splits data/splits --output reports/baseline_benchmark.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.evaluation import format_markdown_report, run_benchmark
from src.data.loader import load_spectrum_records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", default="data/raw/train.parquet")
    parser.add_argument("--splits", default="data/splits")
    parser.add_argument("--output", default="reports/baseline_benchmark.md")
    parser.add_argument("--max-records", type=int, default=None)
    args = parser.parse_args()

    records = load_spectrum_records(args.train, max_records=args.max_records)
    report = format_markdown_report(run_benchmark(records, args.splits))
    print(report)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
