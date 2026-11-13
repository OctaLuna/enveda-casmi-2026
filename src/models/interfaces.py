"""Typed contracts shared by retrieval models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidatePrediction:
    """A candidate structure with its retrieval score and one-based rank."""

    smiles: str
    score: float
    rank: int
