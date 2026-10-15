"""Unified LC-MS/MS spectral preprocessing pipeline for CASMI 2026.

Implements strict physical and chemical cleaning standards:
1. Relative intensity filtering (<1-2% of base peak).
2. Precursor overhang cutoff (m/z > precursor_mz + 2.0 Da).
3. Explicit deisotoping (+1 and +2 Da collapsing).
4. Density control (min 5 peaks for train, mass-window top-k for dense spectra, test fallback).
5. Intensity transformations (sqrt / log1p) with base peak re-normalization.
6. Neutral mass calculation via adduct normalizer.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable

import numpy as np

from src.data.adduct_normalizer import calculate_neutral_mass
from src.data.deisotoper import deisotope_spectrum
from src.data.spectrum_parser import SpectrumRecord

logger = logging.getLogger(__name__)


class SpectrumPreprocessor:
    """Configurable pipeline for preprocessing MS/MS spectra."""

    def __init__(
        self,
        min_relative_intensity: float = 0.01,
        precursor_tolerance_da: float = 2.0,
        deisotope: bool = True,
        deisotope_tolerance_da: float = 0.015,
        min_peaks: int = 5,
        intensity_transform: str = "sqrt",
        max_peaks_per_window: int = 10,
        mass_window_da: float = 50.0,
        max_total_peaks: int = 150,
    ):
        self.min_relative_intensity = min_relative_intensity
        self.precursor_tolerance_da = precursor_tolerance_da
        self.deisotope = deisotope
        self.deisotope_tolerance_da = deisotope_tolerance_da
        self.min_peaks = min_peaks
        self.intensity_transform = intensity_transform.lower()
        self.max_peaks_per_window = max_peaks_per_window
        self.mass_window_da = mass_window_da
        self.max_total_peaks = max_total_peaks

    def get_neutral_mass(self, record: SpectrumRecord) -> float | None:
        """Calculate analyte exact neutral mass using adduct table."""
        return calculate_neutral_mass(record.precursor_mz, record.adduct)

    def _apply_density_window_filter(
        self, mzs: list[float], intensities: list[float]
    ) -> tuple[list[float], list[float]]:
        """Filter peaks by mass window to prevent local peak crowding."""
        if len(mzs) <= self.max_peaks_per_window:
            return mzs, intensities

        # Group peaks into sliding or fixed mass windows
        windows: dict[int, list[tuple[float, float]]] = defaultdict(list)
        for mz, intensity in zip(mzs, intensities):
            win_idx = int(mz // self.mass_window_da)
            windows[win_idx].append((mz, intensity))

        kept_peaks: list[tuple[float, float]] = []
        for win_peaks in windows.values():
            # Sort descending by intensity within window
            win_peaks.sort(key=lambda p: p[1], reverse=True)
            kept_peaks.extend(win_peaks[: self.max_peaks_per_window])

        # If still exceeds max_total_peaks, keep globally most intense
        if len(kept_peaks) > self.max_total_peaks:
            kept_peaks.sort(key=lambda p: p[1], reverse=True)
            kept_peaks = kept_peaks[: self.max_total_peaks]

        # Re-sort chronologically by m/z
        kept_peaks.sort(key=lambda p: p[0])
        return [p[0] for p in kept_peaks], [p[1] for p in kept_peaks]

    def _apply_intensity_transform(self, intensities: list[float]) -> list[float]:
        """Apply mathematical transformation (sqrt or log1p) and normalize base peak to 1.0."""
        arr = np.asarray(intensities, dtype=np.float64)
        if len(arr) == 0:
            return []

        if self.intensity_transform == "sqrt":
            arr = np.sqrt(np.maximum(arr, 0.0))
        elif self.intensity_transform == "log1p":
            arr = np.log1p(np.maximum(arr, 0.0))

        base_peak = np.max(arr)
        if base_peak > 0:
            arr = arr / base_peak

        return arr.tolist()

    def preprocess_record(
        self, record: SpectrumRecord, is_test: bool = False
    ) -> SpectrumRecord | None:
        """Clean and normalize a single SpectrumRecord.

        Args:
            record: Input raw spectrum record.
            is_test: Set to True for test set. Guarantees no spectrum is dropped.

        Returns:
            Preprocessed SpectrumRecord or None if rejected in training mode.
        """
        # Step 1: Filter precursor overhang
        overhang_record = record.filter_precursor_overhang(
            mass_tolerance_da=self.precursor_tolerance_da
        )

        # Step 2: Filter noise peaks
        noise_filtered = overhang_record.filter_noise_peaks(
            relative_intensity_threshold=self.min_relative_intensity
        )

        mzs = noise_filtered.ms2_mzs
        ints = noise_filtered.ms2_normalized_intensities

        # Step 3: Explicit deisotoping
        if self.deisotope and len(mzs) > 1:
            mzs, ints = deisotope_spectrum(
                mzs, ints, mass_tolerance_da=self.deisotope_tolerance_da
            )

        # Step 4: Density check (min peaks constraint)
        if len(mzs) < self.min_peaks:
            if not is_test:
                logger.debug(
                    "Dropping spectrum %s in train: %d peaks (< %d min)",
                    record.spectrum_id,
                    len(mzs),
                    self.min_peaks,
                )
                return None

            # Test fallback: never leave a test molecule with empty predictions
            # Relax noise filtering and recover raw overhang-filtered peaks
            logger.warning(
                "Test spectrum %s has only %d peaks; applying fallback",
                record.spectrum_id,
                len(mzs),
            )
            mzs = overhang_record.ms2_mzs
            ints = overhang_record.ms2_normalized_intensities
            if len(mzs) == 0:
                # Extreme fallback: restore raw peaks
                mzs = record.ms2_mzs
                ints = record.ms2_normalized_intensities

        # Step 5: Density control for hyper-dense spectra
        mzs, ints = self._apply_density_window_filter(mzs, ints)

        # Step 6: Intensity transformation and re-normalization
        ints = self._apply_intensity_transform(ints)

        return SpectrumRecord(
            molecule_id=record.molecule_id,
            spectrum_id=record.spectrum_id,
            ms2_mzs=mzs,
            ms2_normalized_intensities=ints,
            precursor_mz=record.precursor_mz,
            adduct=record.adduct,
            collision_energy_ev=record.collision_energy_ev,
            label=record.label,
        )

    def preprocess_batch(
        self, records: Iterable[SpectrumRecord], is_test: bool = False
    ) -> list[SpectrumRecord]:
        """Preprocess a collection of spectrum records.

        Args:
            records: Iterable of SpectrumRecord objects.
            is_test: True if processing test data.

        Returns:
            List of successfully preprocessed SpectrumRecord objects.
        """
        results: list[SpectrumRecord] = []
        for rec in records:
            cleaned = self.preprocess_record(rec, is_test=is_test)
            if cleaned is not None:
                results.append(cleaned)
        return results
