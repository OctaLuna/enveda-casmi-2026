"""Spectrum data structures and validation parsers for CASMI 2026."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpectrumMetadata:
    """Lightweight identifiers and label used by split generation."""

    molecule_id: str
    spectrum_id: str
    label: str


@dataclass
class SpectrumRecord:
    """Represents a single LC-MS/MS spectrum record from train.parquet or test.parquet."""

    molecule_id: str
    spectrum_id: str
    ms2_mzs: list[float]
    ms2_normalized_intensities: list[float]
    precursor_mz: float
    adduct: str
    collision_energy_ev: float
    label: str | None = None  # Canonical SMILES, present only in train

    def __post_init__(self):
        if len(self.ms2_mzs) != len(self.ms2_normalized_intensities):
            raise ValueError(
                f"Peak array length mismatch for spectrum {self.spectrum_id}: "
                f"{len(self.ms2_mzs)} mzs vs {len(self.ms2_normalized_intensities)} intensities"
            )

    @property
    def peak_count(self) -> int:
        """Return the number of fragmentation peaks."""
        return len(self.ms2_mzs)

    def filter_noise_peaks(
        self, relative_intensity_threshold: float = 0.01
    ) -> "SpectrumRecord":
        """Filter out peaks below relative intensity threshold (e.g. 1% of base peak).

        Args:
            relative_intensity_threshold: Minimum intensity relative to base peak (1.0).

        Returns:
            A new filtered SpectrumRecord instance.
        """
        filtered_mzs = []
        filtered_intensities = []
        for mz, intensity in zip(self.ms2_mzs, self.ms2_normalized_intensities):
            if intensity >= relative_intensity_threshold:
                filtered_mzs.append(mz)
                filtered_intensities.append(intensity)

        return SpectrumRecord(
            molecule_id=self.molecule_id,
            spectrum_id=self.spectrum_id,
            ms2_mzs=filtered_mzs,
            ms2_normalized_intensities=filtered_intensities,
            precursor_mz=self.precursor_mz,
            adduct=self.adduct,
            collision_energy_ev=self.collision_energy_ev,
            label=self.label,
        )

    def filter_precursor_overhang(
        self, mass_tolerance_da: float = 2.0
    ) -> "SpectrumRecord":
        """Discard fragment peaks exceeding precursor_mz + tolerance.

        Args:
            mass_tolerance_da: Isotopic tolerance above precursor_mz in Daltons.

        Returns:
            A new filtered SpectrumRecord instance.
        """
        max_allowed_mz = self.precursor_mz + mass_tolerance_da
        filtered_mzs = []
        filtered_intensities = []
        for mz, intensity in zip(self.ms2_mzs, self.ms2_normalized_intensities):
            if mz <= max_allowed_mz:
                filtered_mzs.append(mz)
                filtered_intensities.append(intensity)

        return SpectrumRecord(
            molecule_id=self.molecule_id,
            spectrum_id=self.spectrum_id,
            ms2_mzs=filtered_mzs,
            ms2_normalized_intensities=filtered_intensities,
            precursor_mz=self.precursor_mz,
            adduct=self.adduct,
            collision_energy_ev=self.collision_energy_ev,
            label=self.label,
        )
