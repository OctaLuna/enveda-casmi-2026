"""Reproducible, memory-conscious anti-leakage splits for CASMI 2026."""

from __future__ import annotations

import datetime
import hashlib
import itertools
import json
import logging
import os
import random
import re
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.data.spectrum_parser import SpectrumMetadata, SpectrumRecord
from src.utils.metrics import get_tautomer_enumerator
from src.utils.reproducibility import set_seed

logger = logging.getLogger(__name__)

DEFAULT_SEEDS = (42, 1337, 2026)
TANIMOTO_NEIGHBOR_NUMERATOR = 2
TANIMOTO_NEIGHBOR_DENOMINATOR = 5
TANIMOTO_NEIGHBOR_THRESHOLD = (
    TANIMOTO_NEIGHBOR_NUMERATOR / TANIMOTO_NEIGHBOR_DENOMINATOR
)
MIN_CLASS3_MEAN_DISTANCE = 0.60
ECFP4_RADIUS = 2
ECFP4_FP_SIZE = 2048
FEATURE_WORKERS = min(4, os.cpu_count() or 1)
FEATURE_BATCH_SIZE = 512


@dataclass
class _MoleculeSummary:
    count: int = 0
    scaffold: str = ""
    fingerprint: Any = None
    query_spectrum_ids: dict[int, str] = field(default_factory=dict)


@lru_cache(maxsize=1)
def _ecfp4_generator() -> Any:
    try:
        from rdkit.Chem import rdFingerprintGenerator
    except ImportError as exc:
        raise RuntimeError(
            "RDKit is required to build structural validation splits."
        ) from exc
    return rdFingerprintGenerator.GetMorganGenerator(
        radius=ECFP4_RADIUS, fpSize=ECFP4_FP_SIZE
    )


def _molecular_features(smiles: str) -> tuple[str, str, Any]:
    """Return tautomer-canonical SMILES, Murcko scaffold, and ECFP4 fingerprint."""
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold
    except ImportError as exc:
        raise RuntimeError(
            "RDKit is required to build structural validation splits."
        ) from exc

    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Invalid training SMILES for split generation: {smiles!r}")
    tautomer_enumerator = get_tautomer_enumerator()
    if tautomer_enumerator:
        from rdkit import rdBase

        with rdBase.BlockLogs():
            molecule = tautomer_enumerator.Canonicalize(molecule)
    canonical_smiles = Chem.MolToSmiles(molecule, canonical=True)

    scaffold = MurckoScaffold.MurckoScaffoldSmiles(
        mol=molecule, includeChirality=False
    )
    if not scaffold:
        scaffold = hashlib.sha256(canonical_smiles.encode("utf-8")).hexdigest()[:16]

    return canonical_smiles, scaffold, _ecfp4_generator().GetFingerprint(molecule)


def _molecular_feature_job(
    job: tuple[str, str],
) -> tuple[str, str, str, Any]:
    molecule_id, smiles = job
    canonical_smiles, scaffold, fingerprint = _molecular_features(smiles)
    return molecule_id, canonical_smiles, scaffold, fingerprint


def _iter_molecular_feature_jobs(
    jobs: Iterable[tuple[str, str]],
    workers: int = FEATURE_WORKERS,
    batch_size: int = FEATURE_BATCH_SIZE,
) -> Iterator[tuple[str, str, str, Any]]:
    """Compute features in bounded batches, preserving input order."""
    if workers < 1:
        raise ValueError("workers must be at least one.")
    if batch_size < 1:
        raise ValueError("batch_size must be at least one.")

    if workers == 1:
        for job in jobs:
            yield _molecular_feature_job(job)
        return

    with ProcessPoolExecutor(max_workers=workers) as executor:
        for job_batch in itertools.batched(jobs, batch_size):
            yield from executor.map(
                _molecular_feature_job,
                job_batch,
                chunksize=min(32, batch_size),
            )


def compute_molecular_scaffold(smiles: str | None) -> str:
    """Compute a Bemis-Murcko scaffold with a deterministic fallback."""
    if not smiles or not smiles.strip():
        return "UNKNOWN_SCAFFOLD"

    clean_smiles = smiles.strip()
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold

        molecule = Chem.MolFromSmiles(clean_smiles)
        if molecule is not None:
            scaffold = MurckoScaffold.MurckoScaffoldSmiles(
                mol=molecule, includeChirality=False
            )
            if scaffold:
                return scaffold
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.debug("Murcko scaffold failed for '%s': %s", smiles, exc)

    return hashlib.sha256(clean_smiles.encode("utf-8")).hexdigest()[:16]


class _ExactTanimotoSearch:
    """Exact Tanimoto search using RDKit's native bulk implementation."""

    def __init__(self, reference_fingerprints: Sequence[Any]):
        if not reference_fingerprints:
            raise ValueError("Tanimoto search requires at least one reference.")

        try:
            import numpy as np
            from rdkit import DataStructs
        except ImportError as exc:
            raise RuntimeError(
                "NumPy and RDKit are required for ECFP4/Tanimoto search."
            ) from exc

        self._np = np
        self._data_structs = DataStructs
        self._reference_fingerprints = tuple(reference_fingerprints)
        fingerprint_size = self._reference_fingerprints[0].GetNumBits()
        if any(
            fingerprint.GetNumBits() != fingerprint_size
            for fingerprint in self._reference_fingerprints
        ):
            raise ValueError("Reference fingerprints have inconsistent sizes.")

    def similarities_for(self, query_fingerprint: Any) -> Any:
        """Return exact similarities to all references as a NumPy vector."""
        if query_fingerprint.GetNumBits() != self._reference_fingerprints[0].GetNumBits():
            raise ValueError("Query and reference fingerprints have different sizes.")
        similarities = self._data_structs.BulkTanimotoSimilarity(
            query_fingerprint, self._reference_fingerprints
        )
        return self._np.fromiter(
            similarities, dtype=self._np.float64, count=len(self._reference_fingerprints)
        )


def _collect_molecule_summaries(
    records: Iterable[SpectrumMetadata | SpectrumRecord],
    seeds: Sequence[int],
) -> dict[str, _MoleculeSummary]:
    """Aggregate metadata, then compute molecular features in parallel batches."""
    summaries: dict[str, _MoleculeSummary] = {}
    molecular_smiles: dict[str, str] = {}
    query_rngs = {seed: random.Random(seed) for seed in seeds}

    for record in records:
        molecule_id = str(record.molecule_id)
        spectrum_id = str(record.spectrum_id)
        label = record.label
        if not label or not label.strip():
            raise ValueError(f"Missing training label for molecule {molecule_id!r}")

        summary = summaries.get(molecule_id)
        if summary is None:
            summary = _MoleculeSummary()
            summaries[molecule_id] = summary
            molecular_smiles[molecule_id] = label.strip()

        new_count = summary.count + 1
        for seed, rng in query_rngs.items():
            # Reservoir sampling selects one spectrum uniformly without storing IDs.
            if new_count == 1 or rng.randrange(new_count) == 0:
                summary.query_spectrum_ids[seed] = spectrum_id
        summary.count = new_count

    if not summaries:
        raise ValueError("Cannot split an empty training dataset.")

    logger.info(
        "Canonicalizando y calculando ECFP4 para %d moléculas con %d procesos.",
        len(molecular_smiles),
        FEATURE_WORKERS,
    )
    feature_count = len(molecular_smiles)
    for feature_index, (molecule_id, _, scaffold, fingerprint) in enumerate(
        _iter_molecular_feature_jobs(
            molecular_smiles.items(),
            workers=FEATURE_WORKERS,
            batch_size=FEATURE_BATCH_SIZE,
        ),
        start=1,
    ):
        summary = summaries[molecule_id]
        summary.scaffold = scaffold
        summary.fingerprint = fingerprint
        if feature_index % 5000 == 0 or feature_index == feature_count:
            logger.info(
                "Features moleculares: %d/%d.", feature_index, feature_count
            )
    return summaries


def compute_mean_nearest_neighbor_tanimoto_distance(
    query_molecule_ids: Sequence[str],
    reference_molecule_ids: Sequence[str],
    fingerprints: dict[str, Any],
) -> float:
    """Average 1 - maximum ECFP4 Tanimoto similarity from each query to train."""
    if not query_molecule_ids:
        raise ValueError("Val-Clase3 must contain at least one molecule.")
    if not reference_molecule_ids:
        raise ValueError("Train must contain molecules for the Tanimoto audit.")

    search = _ExactTanimotoSearch(
        [fingerprints[molecule_id] for molecule_id in reference_molecule_ids]
    )
    distances: list[float] = []
    query_count = len(query_molecule_ids)
    logger.info("Midiendo distancia Tanimoto exacta para %d moléculas.", query_count)
    for query_index, molecule_id in enumerate(query_molecule_ids, start=1):
        similarities = search.similarities_for(fingerprints[molecule_id])
        nearest_similarity = float(similarities.max())
        distances.append(1.0 - nearest_similarity)
        if query_index % 1000 == 0 or query_index == query_count:
            logger.info(
                "Distancia Tanimoto exacta: %d/%d moléculas.",
                query_index,
                query_count,
            )
    return sum(distances) / len(distances)


def _split_summaries(
    summaries: dict[str, _MoleculeSummary],
    seed: int,
    val_clase1_ratio: float,
    val_clase2_ratio: float,
    val_clase3_ratio: float,
    source_sha256: str | None,
    fingerprints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rng = random.Random(seed)
    all_molecule_ids = sorted(summaries)
    scaffold_groups: dict[str, list[str]] = defaultdict(list)
    for molecule_id in all_molecule_ids:
        scaffold_groups[summaries[molecule_id].scaffold].append(molecule_id)

    # Val-Clase3 takes entire Murcko groups, giving every seed a genuine
    # out-of-scaffold structural holdout.
    scaffold_keys = sorted(scaffold_groups)
    rng.shuffle(scaffold_keys)
    target_class3_count = max(
        1, int(len(all_molecule_ids) * val_clase3_ratio)
    )
    val_clase3_molecules: set[str] = set()
    for scaffold in scaffold_keys:
        val_clase3_molecules.update(scaffold_groups[scaffold])
        if len(val_clase3_molecules) >= target_class3_count:
            break

    # Remove the complete Murcko groups of all train candidates whose ECFP4
    # similarity to any Val-Clase3 molecule is >= 0.40.
    reference_molecules = [
        molecule_id
        for molecule_id in all_molecule_ids
        if molecule_id not in val_clase3_molecules
    ]
    reference_fingerprints = [
        summaries[molecule_id].fingerprint for molecule_id in reference_molecules
    ]
    reference_search = _ExactTanimotoSearch(reference_fingerprints)
    excluded_scaffolds: set[str] = set()
    val_clase3_query_ids = sorted(val_clase3_molecules)
    logger.info(
        "Semilla %d: buscando vecinos de %d moléculas Val-Clase3.",
        seed,
        len(val_clase3_query_ids),
    )
    for query_index, query_id in enumerate(val_clase3_query_ids, start=1):
        similarities = reference_search.similarities_for(
            summaries[query_id].fingerprint
        )
        close_indices = reference_search._np.flatnonzero(
            similarities >= TANIMOTO_NEIGHBOR_THRESHOLD
        )
        for index in close_indices:
            candidate_id = reference_molecules[int(index)]
            excluded_scaffolds.add(summaries[candidate_id].scaffold)
        if query_index % 1000 == 0 or query_index == len(val_clase3_query_ids):
            logger.info(
                "Semilla %d: búsqueda de vecinos %d/%d.",
                seed,
                query_index,
                len(val_clase3_query_ids),
            )

    excluded_neighbor_molecules = {
        molecule_id
        for scaffold in excluded_scaffolds
        for molecule_id in scaffold_groups[scaffold]
        if molecule_id not in val_clase3_molecules
    }
    train_candidates = set(reference_molecules) - excluded_neighbor_molecules

    # Val-Clase1 keeps the molecule's other spectra in the retrieval library;
    # its held-out query is recorded separately.
    multi_spectrum_molecules = sorted(
        molecule_id
        for molecule_id in train_candidates
        if summaries[molecule_id].count >= 2
    )
    rng.shuffle(multi_spectrum_molecules)
    if not multi_spectrum_molecules:
        raise ValueError("No multi-spectrum molecules remain for Val-Clase1.")
    class1_count = min(
        len(multi_spectrum_molecules),
        max(1, int(len(multi_spectrum_molecules) * val_clase1_ratio)),
    )
    val_clase1_molecules = set(multi_spectrum_molecules[:class1_count])
    val_clase1_query_spectrum_ids = sorted(
        summaries[molecule_id].query_spectrum_ids[seed]
        for molecule_id in val_clase1_molecules
    )

    remaining_molecules = sorted(train_candidates - val_clase1_molecules)
    if not remaining_molecules:
        raise ValueError("No molecules remain for Val-Clase2 and train.")
    rng.shuffle(remaining_molecules)
    class2_count = min(
        len(remaining_molecules),
        max(1, int(len(remaining_molecules) * val_clase2_ratio)),
    )
    val_clase2_molecules = set(remaining_molecules[:class2_count])
    train_molecules = sorted(train_candidates - val_clase2_molecules)
    if not train_molecules:
        raise ValueError("Structural exclusions left no molecules in train.")

    del reference_search
    fingerprint_map = fingerprints or {
        molecule_id: summary.fingerprint
        for molecule_id, summary in summaries.items()
    }
    mean_class3_distance = compute_mean_nearest_neighbor_tanimoto_distance(
        sorted(val_clase3_molecules),
        train_molecules,
        fingerprint_map,
    )
    if mean_class3_distance <= MIN_CLASS3_MEAN_DISTANCE:
        raise ValueError(
            "Val-Clase3 failed its nearest-train distance criterion: "
            f"mean distance {mean_class3_distance:.4f} must be > "
            f"{MIN_CLASS3_MEAN_DISTANCE:.2f}."
        )

    metadata: dict[str, Any] = {
        "seed": seed,
        "n_total_molecules": len(all_molecule_ids),
        "n_total_spectra": sum(summary.count for summary in summaries.values()),
        "n_train_molecules": len(train_molecules),
        "n_train_spectra": sum(summaries[mid].count for mid in train_molecules)
        - len(val_clase1_query_spectrum_ids),
        "n_val_clase1_molecules": len(val_clase1_molecules),
        "n_val_clase2_molecules": len(val_clase2_molecules),
        "n_val_clase3_molecules": len(val_clase3_molecules),
        "n_excluded_neighbor_molecules": len(excluded_neighbor_molecules),
        "tanimoto_neighbor_threshold": TANIMOTO_NEIGHBOR_THRESHOLD,
        "mean_val_clase3_nearest_train_tanimoto_distance": mean_class3_distance,
        "created_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    if source_sha256 is not None:
        metadata["train_sha256"] = source_sha256

    return {
        "schema_version": 1,
        "train_molecule_ids": train_molecules,
        "val_clase1_molecule_ids": sorted(val_clase1_molecules),
        "val_clase1_query_spectrum_ids": val_clase1_query_spectrum_ids,
        "val_clase2_molecule_ids": sorted(val_clase2_molecules),
        "val_clase3_molecule_ids": sorted(val_clase3_molecules),
        "val_clase3_excluded_neighbor_molecule_ids": sorted(
            excluded_neighbor_molecules
        ),
        "metadata": metadata,
    }


class StructuralSplitter:
    """Generate the three CASMI validation classes without retaining peak arrays."""

    def __init__(
        self,
        seed: int = 42,
        val_clase1_ratio: float = 0.15,
        val_clase2_ratio: float = 0.10,
        val_clase3_ratio: float = 0.10,
    ):
        for name, ratio in (
            ("val_clase1_ratio", val_clase1_ratio),
            ("val_clase2_ratio", val_clase2_ratio),
            ("val_clase3_ratio", val_clase3_ratio),
        ):
            if not 0.0 <= ratio <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")
        self.seed = seed
        self.val_clase1_ratio = val_clase1_ratio
        self.val_clase2_ratio = val_clase2_ratio
        self.val_clase3_ratio = val_clase3_ratio

    def split(
        self,
        records: Iterable[SpectrumMetadata | SpectrumRecord],
    ) -> dict[str, Any]:
        """Split a one-pass iterable of spectrum metadata or records."""
        set_seed(42)
        summaries = _collect_molecule_summaries(records, (self.seed,))
        fingerprints = {
            molecule_id: summary.fingerprint
            for molecule_id, summary in summaries.items()
        }
        return _split_summaries(
            summaries,
            seed=self.seed,
            val_clase1_ratio=self.val_clase1_ratio,
            val_clase2_ratio=self.val_clase2_ratio,
            val_clase3_ratio=self.val_clase3_ratio,
            source_sha256=None,
            fingerprints=fingerprints,
        )


def iter_records_for_split(
    records: Iterable[SpectrumMetadata | SpectrumRecord],
    split_manifest: dict[str, Any],
    partition: str,
) -> Iterator[SpectrumMetadata | SpectrumRecord]:
    """Rebuild a spectrum-level partition from a compact molecule manifest."""
    if split_manifest.get("schema_version") != 1:
        raise ValueError("Unsupported split manifest schema_version.")
    partition_keys = {
        "val_clase1": "val_clase1_query_spectrum_ids",
        "val_clase2": "val_clase2_molecule_ids",
        "val_clase3": "val_clase3_molecule_ids",
    }
    if partition != "train" and partition not in partition_keys:
        raise ValueError(
            "partition must be train, val_clase1, val_clase2, or val_clase3."
        )

    train_molecules = set(split_manifest["train_molecule_ids"])
    query_spectrum_ids = set(split_manifest["val_clase1_query_spectrum_ids"])
    if partition == "train":
        for record in records:
            if (
                record.molecule_id in train_molecules
                and record.spectrum_id not in query_spectrum_ids
            ):
                yield record
        return

    field = partition_keys[partition]
    selected_ids = set(split_manifest[field])
    for record in records:
        value = (
            record.spectrum_id
            if partition == "val_clase1"
            else record.molecule_id
        )
        if value in selected_ids:
            yield record


def _manifest_size_limit_bytes() -> int:
    """Read the per-file Git limit from the project agent configuration."""
    config_path = Path(__file__).resolve().parents[2] / ".agents" / "project.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        limit_mb = int(config["large_file_mb"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        limit_mb = 25
    return limit_mb * 1024 * 1024


def generate_and_save_splits(
    records: Iterable[SpectrumMetadata | SpectrumRecord],
    output_dir: str | Path = "data/splits",
    seeds: Sequence[int] = DEFAULT_SEEDS,
    source_sha256: str | None = None,
) -> dict[int, Path]:
    """Write compact manifests for at least three deterministic split seeds."""
    seed_values = tuple(int(seed) for seed in seeds)
    if len(seed_values) != 3 or set(seed_values) != set(DEFAULT_SEEDS):
        raise ValueError("Split manifests require exactly seeds 42, 1337, and 2026.")
    if source_sha256 is not None and not re.fullmatch(
        r"[0-9a-fA-F]{64}", source_sha256
    ):
        raise ValueError("source_sha256 must contain exactly 64 hexadecimal digits.")

    set_seed(42)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    summaries = _collect_molecule_summaries(records, seed_values)
    fingerprints = {
        molecule_id: summary.fingerprint
        for molecule_id, summary in summaries.items()
    }
    limit_bytes = _manifest_size_limit_bytes()

    pending: dict[int, tuple[Path, Path]] = {}
    try:
        for seed in seed_values:
            split_data = _split_summaries(
                summaries,
                seed=seed,
                val_clase1_ratio=0.15,
                val_clase2_ratio=0.10,
                val_clase3_ratio=0.10,
                source_sha256=source_sha256,
                fingerprints=fingerprints,
            )
            target_file = out_path / f"split_seed_{seed}.json"
            payload = json.dumps(
                split_data, ensure_ascii=False, separators=(",", ":"), sort_keys=True
            ).encode("utf-8")
            if len(payload) > limit_bytes:
                raise ValueError(
                    f"{target_file.name} is {len(payload)} bytes; project limit is "
                    f"{limit_bytes} bytes."
                )

            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=out_path,
                prefix=f".{target_file.stem}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_file.write(payload)
                pending[seed] = (Path(temp_file.name), target_file)

        manifest_paths: dict[int, Path] = {}
        for seed, (temp_path, target_file) in pending.items():
            temp_path.replace(target_file)
            manifest_paths[seed] = target_file
        return manifest_paths
    except Exception:
        for temp_path, _ in pending.values():
            temp_path.unlink(missing_ok=True)
        raise
