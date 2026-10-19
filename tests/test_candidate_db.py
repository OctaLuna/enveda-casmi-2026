"""Unit tests for offline candidate database indexed by molecular formula."""

import pytest

from src.data.candidate_db import CandidateDatabase


@pytest.fixture
def empty_db():
    return CandidateDatabase()


def test_add_and_query_by_formula(empty_db):
    # Add caffeine C8H10N4O2
    caffeine_smi = "Cn1cnc2c1c(=O)n(c(=O)n2C)C"
    empty_db.add_candidate(smiles=caffeine_smi, source="PubChem")

    # Add theobromine C7H8N4O2
    theobromine_smi = "Cn1cnc2c1c(=O)[nH]c(=O)n2C"
    empty_db.add_candidate(smiles=theobromine_smi, source="COCONUT")

    # Query caffeine formula
    candidates_caffeine = empty_db.get_candidates("C8H10N4O2")
    assert len(candidates_caffeine) == 1
    assert candidates_caffeine[0].formula == "C8H10N4O2"
    assert "PubChem" in candidates_caffeine[0].sources

    # Query theobromine formula
    candidates_theo = empty_db.get_candidates("C7H8N4O2")
    assert len(candidates_theo) == 1
    assert candidates_theo[0].formula == "C7H8N4O2"
    assert "COCONUT" in candidates_theo[0].sources

    # Query non-existent formula
    assert empty_db.get_candidates("C99H99N99") == []


def test_deduplication_by_inchikey14_merges_sources(empty_db):
    smi = "c1ccccc1O"  # Phenol C6H6O
    empty_db.add_candidate(smiles=smi, source="PubChem")
    empty_db.add_candidate(smiles=smi, source="LOTUS")

    candidates = empty_db.get_candidates("C6H6O")
    assert len(candidates) == 1
    rec = candidates[0]
    assert rec.sources == ["LOTUS", "PubChem"] or set(rec.sources) == {
        "PubChem",
        "LOTUS",
    }


def test_save_and_load_parquet(tmp_path):
    db1 = CandidateDatabase()
    db1.add_candidate("CCO", source="PubChem")
    db1.add_candidate("c1ccccc1", source="COCONUT")

    parquet_file = tmp_path / "candidates.parquet"
    db1.save_to_parquet(parquet_file)
    assert parquet_file.exists()

    db2 = CandidateDatabase.load_from_parquet(parquet_file)
    assert len(db2.get_candidates("C2H6O")) == 1
    assert len(db2.get_candidates("C6H6")) == 1
    assert db2.size == 2
