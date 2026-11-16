"""Local 3-class benchmark of the baseline pipeline (MRR@25 per validation subset)."""

import json
import statistics
from time import perf_counter
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from src.api.baseline_pipeline import BaselinePipeline
from src.data.spectrum_parser import SpectrumRecord
from src.models.baseline_agent import BaselineSpectralMatcher
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


def compare_class1_strategies(
    records: Sequence[SpectrumRecord],
    split: dict[str, Any],
    fusion_weights: tuple[float, float] = (0.5, 0.5),
) -> dict[str, dict[str, float]]:
    """Compare cosine and fixed weighted fusion on one held-out Class-1 split."""
    by_id = {record.spectrum_id: record for record in records}
    query_ids = set(split.get(CLASS_QUERY_KEYS["Val-Clase1"], []))
    missing_query_ids = query_ids - by_id.keys()
    if missing_query_ids:
        raise ValueError(
            f"Val-Clase1 query spectra are missing from records: "
            f"{len(missing_query_ids)} of {len(query_ids)}"
        )
    train_molecules = set(split["train_molecule_ids"])
    queries = [by_id[s] for s in sorted(query_ids)]
    if any(query.molecule_id not in train_molecules for query in queries):
        raise ValueError("Val-Clase1 query molecules must belong to train_molecule_ids")
    library = [
        record
        for record in records
        if record.molecule_id in train_molecules and record.spectrum_id not in query_ids
    ]
    truth: dict[str, str] = {}
    for query in queries:
        if not query.label:
            raise ValueError(
                f"Val-Clase1 query {query.spectrum_id} has no ground-truth label"
            )
        if query.molecule_id in truth:
            raise ValueError(
                "Val-Clase1 manifest must select at most one query per molecule"
            )
        truth[query.molecule_id] = query.molecule_id

    # The official train data exposes molecule_id as InChIKey14. Mapping each
    # retrieved train label back to that key reproduces the competition's
    # identity match without requiring RDKit in Kaggle's offline image.
    label_to_molecule_id: dict[str, str] = {}
    for record in library:
        if record.label is None:
            continue
        prior_id = label_to_molecule_id.setdefault(record.label, record.molecule_id)
        if prior_id != record.molecule_id:
            raise ValueError(
                f"Training label {record.label!r} maps to multiple molecule IDs"
            )

    results = {}
    for strategy in ("cosine", "weighted_fusion"):
        matcher = BaselineSpectralMatcher(
            strategy=strategy,
            cosine_weight=fusion_weights[0],
            entropy_weight=fusion_weights[1],
        ).fit(library)
        started = perf_counter()
        predictions = {
            query.molecule_id: matcher.predict_top_k(query) for query in queries
        }
        elapsed = perf_counter() - started
        molecules = sorted(truth)
        candidate_ids = []
        for molecule_id in molecules:
            seen: set[str] = set()
            ranked_ids = []
            for label in predictions.get(molecule_id, []):
                candidate_id = label_to_molecule_id.get(label)
                if candidate_id is None:
                    raise ValueError(
                        f"Predicted label {label!r} has no training molecule ID"
                    )
                if candidate_id not in seen:
                    seen.add(candidate_id)
                    ranked_ids.append(candidate_id)
                    if len(ranked_ids) == 25:
                        break
            candidate_ids.append(ranked_ids)
        results[strategy] = {
            "mrr_at_25": calculate_mrr_at_25(
                [truth[m] for m in molecules],
                candidate_ids,
                use_inchikey14=False,
                deduplicate_candidates=False,
            ),
            "mean_latency_ms": elapsed * 1000 / max(len(queries), 1),
            "query_count": float(len(queries)),
            "cosine_weight": (
                fusion_weights[0] if strategy == "weighted_fusion" else 1.0
            ),
            "entropy_weight": (
                fusion_weights[1] if strategy == "weighted_fusion" else 0.0
            ),
        }
    return results


def format_strategy_comparison(results: dict[str, dict[str, float]], seed: int) -> str:
    lines = [
        "# Val-Clase1 strategy comparison",
        "",
        f"Split seed: {seed}",
        "",
        "| Strategy | Weights (cosine, entropy) | MRR@25 | Mean latency (ms/query) | Queries |",
        "|---|---:|---:|---:|---:|",
    ]
    for strategy, values in results.items():
        weights = f"{values['cosine_weight']:.2f}, {values['entropy_weight']:.2f}"
        lines.append(
            f"| {strategy} | {weights} | {values['mrr_at_25']:.4f} | "
            f"{values['mean_latency_ms']:.3f} | {int(values['query_count'])} |"
        )
    return "\n".join(lines) + "\n"
