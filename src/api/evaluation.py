"""Local 3-class benchmark of the baseline pipeline (MRR@25 per validation subset)."""

import json
import statistics
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from src.api.baseline_pipeline import BaselinePipeline
from src.data.spectrum_parser import SpectrumRecord
from src.utils.metrics import calculate_mrr_at_25
from src.utils.reproducibility import set_seed

# Split-manifest key holding the query spectra of each validation class.
CLASS_QUERY_KEYS: dict[str, str] = {
    "Val-Clase1": "val_clase1_query_spectrum_ids",
    "Val-Clase2": "val_clase2_spectrum_ids",
    "Val-Clase3": "val_clase3_spectrum_ids",
}


def evaluate_split(
    records: Sequence[SpectrumRecord], split: dict[str, Any]
) -> dict[str, float]:
    """Score one split manifest: index train spectra, query each class, MRR@25."""
    set_seed(42)
    by_id = {r.spectrum_id: r for r in records}
    library = [by_id[s] for s in split["train_spectrum_ids"] if s in by_id]
    pipeline = BaselinePipeline().fit(library)

    scores: dict[str, float] = {}
    for class_name, key in CLASS_QUERY_KEYS.items():
        queries = [by_id[s] for s in split.get(key, []) if s in by_id]
        truth: dict[str, str] = {}
        for q in queries:
            if q.label:
                truth.setdefault(q.molecule_id, q.label)
        preds = pipeline.predict(queries)
        mol_ids = sorted(truth)
        scores[class_name] = calculate_mrr_at_25(
            [truth[m] for m in mol_ids], [preds.get(m, []) for m in mol_ids]
        )
    return scores


def run_benchmark(
    records: Sequence[SpectrumRecord],
    splits_dir: str | Path,
    seeds: Sequence[int] = (42, 1337, 2026),
) -> dict[str, dict[str, Any]]:
    """Evaluate every seed's split and aggregate mean/std per class."""
    per_class: dict[str, dict[int, float]] = defaultdict(dict)
    for seed in seeds:
        path = Path(splits_dir) / f"split_seed_{seed}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Split manifest not found: {path}. Generate it with "
                "src.data.splitter.generate_and_save_splits (DEV1-T3.3)."
            )
        with open(path, encoding="utf-8") as f:
            split = json.load(f)
        for class_name, score in evaluate_split(records, split).items():
            per_class[class_name][seed] = score

    result: dict[str, dict[str, Any]] = {}
    for class_name, by_seed in per_class.items():
        values = list(by_seed.values())
        result[class_name] = {
            "mean": statistics.fmean(values),
            "std": statistics.pstdev(values),
            "by_seed": dict(by_seed),
        }
    return result


def format_markdown_report(result: dict[str, dict[str, Any]]) -> str:
    """Render the benchmark result as a markdown table."""
    lines = [
        "# Baseline benchmark (MRR@25)",
        "",
        "| Subset | MRR@25 medio | Desv. est. | Por semilla |",
        "|---|---|---|---|",
    ]
    for class_name in CLASS_QUERY_KEYS:
        if class_name not in result:
            continue
        r = result[class_name]
        seeds = ", ".join(f"{s}: {v:.4f}" for s, v in sorted(r["by_seed"].items()))
        lines.append(f"| {class_name} | {r['mean']:.4f} | {r['std']:.4f} | {seeds} |")
    return "\n".join(lines) + "\n"
