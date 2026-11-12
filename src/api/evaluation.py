"""Local 3-class benchmark of the baseline pipeline (MRR@25 per validation subset)."""

import json
import random
import statistics
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
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


def _score_class(
    pipeline: BaselinePipeline, queries: Sequence[SpectrumRecord]
) -> float:
    """MRR@25 of one validation class (ground truth = label of each molecule)."""
    truth: dict[str, str] = {}
    for q in queries:
        if q.label:
            truth.setdefault(q.molecule_id, q.label)
    preds = pipeline.predict(queries)
    mol_ids = sorted(truth)
    return calculate_mrr_at_25(
        [truth[m] for m in mol_ids], [preds.get(m, []) for m in mol_ids]
    )


def _cap(ids: Sequence[str], limit: int | None, rng: random.Random) -> set[str]:
    """Deterministic subsample of ids (all of them when no limit applies)."""
    ordered = sorted(ids)
    if limit is None or limit >= len(ordered):
        return set(ordered)
    return set(rng.sample(ordered, limit))


def _evaluate_compact(
    records: Iterable[SpectrumRecord],
    split: dict[str, Any],
    max_queries_per_class: int | None,
) -> dict[str, float]:
    """Score a compact (schema_version 1) manifest in a single pass over records.

    Library = spectra of train molecules minus the Val-Clase1 query spectra.
    Val-Clase1 queries are those spectra; Val-Clase2/3 use one spectrum per
    sampled molecule (never in the library).
    """
    seed = int(split.get("metadata", {}).get("seed", 42))
    rng = random.Random(seed)
    train_mols = set(split["train_molecule_ids"])
    all_q1 = set(split["val_clase1_query_spectrum_ids"])
    q1 = _cap(split["val_clase1_query_spectrum_ids"], max_queries_per_class, rng)
    mols2 = _cap(split["val_clase2_molecule_ids"], max_queries_per_class, rng)
    mols3 = _cap(split["val_clase3_molecule_ids"], max_queries_per_class, rng)

    library: list[SpectrumRecord] = []
    queries: dict[str, list[SpectrumRecord]] = {name: [] for name in CLASS_QUERY_KEYS}
    seen2: set[str] = set()
    seen3: set[str] = set()
    for rec in records:
        if rec.molecule_id in train_mols and rec.spectrum_id not in all_q1:
            library.append(rec)
        if rec.spectrum_id in q1:
            queries["Val-Clase1"].append(rec)
        elif rec.molecule_id in mols2 and rec.molecule_id not in seen2:
            seen2.add(rec.molecule_id)
            queries["Val-Clase2"].append(rec)
        elif rec.molecule_id in mols3 and rec.molecule_id not in seen3:
            seen3.add(rec.molecule_id)
            queries["Val-Clase3"].append(rec)

    pipeline = BaselinePipeline().fit(library)
    return {name: _score_class(pipeline, qs) for name, qs in queries.items()}


def evaluate_split(
    records: Iterable[SpectrumRecord],
    split: dict[str, Any],
    max_queries_per_class: int | None = None,
) -> dict[str, float]:
    """Score one split manifest: index train spectra, query each class, MRR@25.

    Accepts the compact manifest (``schema_version`` 1, molecule ids) over a
    streamed ``records`` iterable, or the legacy one listing spectrum ids.
    """
    set_seed(42)
    if split.get("schema_version") == 1:
        return _evaluate_compact(records, split, max_queries_per_class)

    by_id = {r.spectrum_id: r for r in records}
    library = [by_id[s] for s in split["train_spectrum_ids"] if s in by_id]
    pipeline = BaselinePipeline().fit(library)
    return {
        class_name: _score_class(
            pipeline, [by_id[s] for s in split.get(key, []) if s in by_id]
        )
        for class_name, key in CLASS_QUERY_KEYS.items()
    }


def run_benchmark(
    records: Sequence[SpectrumRecord] | Callable[[], Iterable[SpectrumRecord]],
    splits_dir: str | Path,
    seeds: Sequence[int] = (42, 1337, 2026),
    max_queries_per_class: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Evaluate every seed's split and aggregate mean/std per class.

    ``records`` may be a factory returning a fresh record stream, so each seed
    re-reads the data instead of holding millions of spectra in memory.
    """
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
        seed_records = records() if callable(records) else records
        scores = evaluate_split(seed_records, split, max_queries_per_class)
        for class_name, score in scores.items():
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
