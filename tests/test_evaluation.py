"""Unit tests for the 3-class baseline benchmark (DEV3-T4.3)."""

import json
from pathlib import Path

import pytest

from src.api.evaluation import evaluate_split, format_markdown_report, run_benchmark
from src.data.spectrum_parser import SpectrumRecord

ETHANOL = "CCO"
PROPANE = "CCC"
BENZENE = "c1ccccc1"


def _rec(mol: str, spec: str, mz: float, label: str) -> SpectrumRecord:
    return SpectrumRecord(
        molecule_id=mol,
        spectrum_id=spec,
        ms2_mzs=[mz - 100.0 + 10.0 * i for i in range(6)],
        ms2_normalized_intensities=[0.2, 0.4, 0.6, 0.8, 0.9, 1.0],
        precursor_mz=mz,
        adduct="[M+H]+",
        collision_energy_ev=20.0,
        label=label,
    )


@pytest.fixture
def records() -> list[SpectrumRecord]:
    return [
        _rec("m1", "m1_a", 300.0, ETHANOL),  # train copy of a Clase1 molecule
        _rec("m1", "m1_b", 300.1, ETHANOL),  # Clase1 query
        _rec("m2", "m2_a", 500.0, PROPANE),  # Clase2 (molecule absent from index)
        _rec("m3", "m3_a", 700.0, BENZENE),  # Clase3 (no neighbours)
        _rec("m4", "m4_a", 500.0, "CCCC"),  # train, near m2 but wrong structure
    ]


@pytest.fixture
def split() -> dict:
    return {
        "train_spectrum_ids": ["m1_a", "m4_a"],
        "val_clase1_query_spectrum_ids": ["m1_b"],
        "val_clase2_spectrum_ids": ["m2_a"],
        "val_clase3_spectrum_ids": ["m3_a"],
        "metadata": {"seed": 42},
    }


def test_evaluate_split_scores_each_class(records, split):
    scores = evaluate_split(records, split)
    assert scores["Val-Clase1"] == 1.0
    assert scores["Val-Clase2"] == 0.0  # propane never retrievable
    assert scores["Val-Clase3"] == 0.0


def test_run_benchmark_reads_split_files_and_averages(records, split, tmp_path: Path):
    for seed in (42, 1337):
        (tmp_path / f"split_seed_{seed}.json").write_text(json.dumps(split))
    result = run_benchmark(records, tmp_path, seeds=(42, 1337))
    assert result["Val-Clase1"]["mean"] == 1.0
    assert result["Val-Clase1"]["std"] == 0.0
    assert set(result["Val-Clase1"]["by_seed"]) == {42, 1337}


def test_run_benchmark_missing_split_gives_clear_error(records, tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="split_seed_42.json"):
        run_benchmark(records, tmp_path, seeds=(42,))


def test_markdown_report_contains_three_scores(records, split, tmp_path: Path):
    (tmp_path / "split_seed_42.json").write_text(json.dumps(split))
    result = run_benchmark(records, tmp_path, seeds=(42,))
    md = format_markdown_report(result)
    for name in ("Val-Clase1", "Val-Clase2", "Val-Clase3"):
        assert name in md
    assert "MRR@25" in md
