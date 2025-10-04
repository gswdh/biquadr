"""
Data models for the Biquadr frequency response design application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
import numpy as np
from scipy.signal import butter, sosfreqz


class DataType(Enum):
    """Supported data types for filter coefficients."""

    FLOAT32 = "float32"
    FLOAT64 = "float64"
    INT16 = "int16"
    INT32 = "int32"


class FilterType(Enum):
    """Supported filter types."""

    HIGHPASS = "highpass"
    LOWPASS = "lowpass"


@dataclass
class Target:
    """Represents a target system for filter deployment."""

    name: str
    data_type: DataType
    max_filter_order: int

    def __post_init__(self):
        if self.max_filter_order < 2 or self.max_filter_order > 32:
            raise ValueError("Filter order must be between 2 and 32")


@dataclass
class Filter:
    """Represents a single filter in a project."""

    name: str
    filter_type: FilterType
    order: int
    frequency: float  # Cutoff frequency in Hz
    enabled: bool = True

    def __post_init__(self):
        if self.order < 2 or self.order > 32:
            raise ValueError("Filter order must be between 2 and 32")
        if self.frequency <= 0:
            raise ValueError("Frequency must be positive")


@dataclass
class Channel:
    """Represents a channel within a project (e.g., woofer, mid, tweeter)."""

    name: str
    filters: List[Filter]
    enabled: bool = True

    def add_filter(self, filter_obj: Filter) -> None:
        """Add a filter to the channel."""
        self.filters.append(filter_obj)

    def remove_filter(self, filter_name: str) -> bool:
        """Remove a filter by name. Returns True if removed, False if not found."""
        for i, filter_obj in enumerate(self.filters):
            if filter_obj.name == filter_name:
                del self.filters[i]
                return True
        return False

    def get_enabled_filters(self) -> List[Filter]:
        """Get all enabled filters."""
        return [f for f in self.filters if f.enabled]

    def calculate_frequency_response(
        self, frequencies: np.ndarray, sample_rate: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate the combined frequency response of all enabled filters in this channel.
        Returns (magnitude_db, phase_degrees).
        """
        if not self.get_enabled_filters():
            # Return flat response if no filters
            return np.zeros_like(frequencies), np.zeros_like(frequencies)

        # Calculate individual filter responses
        total_magnitude = np.ones_like(frequencies, dtype=complex)

        for filter_obj in self.get_enabled_filters():
            # Design Butterworth filter
            nyquist = sample_rate / 2
            normalized_freq = filter_obj.frequency / nyquist

            if filter_obj.filter_type == FilterType.LOWPASS:
                btype = "low"
            else:  # HIGHPASS
                btype = "high"

            # Design filter
            sos = butter(filter_obj.order, normalized_freq, btype=btype, output="sos")

            # Calculate frequency response
            _, h = sosfreqz(sos, worN=frequencies * 2 * np.pi / sample_rate)

            # Accumulate response
            total_magnitude *= h

        # Convert to magnitude and phase
        magnitude_db = 20 * np.log10(np.abs(total_magnitude))
        phase_degrees = np.angle(total_magnitude) * 180 / np.pi

        return magnitude_db, phase_degrees

    def calculate_biquad_coefficients(self) -> List[dict]:
        """
        Calculate biquad coefficients for all enabled filters in this channel.
        Returns a list of dictionaries, each containing the coefficients for one biquad section.
        """
        coefficients = []

        for filter_obj in self.get_enabled_filters():
            # Design Butterworth filter
            nyquist = 48000.0 / 2  # Default sample rate, will be overridden
            normalized_freq = filter_obj.frequency / nyquist

            if filter_obj.filter_type == FilterType.LOWPASS:
                btype = "low"
            else:  # HIGHPASS
                btype = "high"

            # Design filter
            sos = butter(filter_obj.order, normalized_freq, btype=btype, output="sos")

            # Convert SOS to biquad coefficients
            for section in sos:
                b0, b1, b2, a0, a1, a2 = section

                # Normalize by a0
                b0 /= a0
                b1 /= a0
                b2 /= a0
                a1 /= a0
                a2 /= a0
                a0 = 1.0

                # Convert to float64 by default (will be converted in export)
                dtype = np.dtype("float64")

                coeff_dict = {
                    "channel_name": self.name,
                    "filter_name": filter_obj.name,
                    "filter_type": filter_obj.filter_type.value,
                    "b0": dtype.type(b0),
                    "b1": dtype.type(b1),
                    "b2": dtype.type(b2),
                    "a1": dtype.type(a1),
                    "a2": dtype.type(a2),
                }
                coefficients.append(coeff_dict)

        return coefficients


@dataclass
class Project:
    """Represents a complete filter project."""

    name: str
    channels: List[Channel]
    sample_rate: float = 48000.0  # Default sample rate

    def add_channel(self, channel: Channel) -> None:
        """Add a channel to the project."""
        self.channels.append(channel)

    def remove_channel(self, channel_name: str) -> bool:
        """Remove a channel by name. Returns True if removed, False if not found."""
        for i, channel in enumerate(self.channels):
            if channel.name == channel_name:
                del self.channels[i]
                return True
        return False

    def get_channel(self, channel_name: str) -> Channel:
        """Get a channel by name."""
        for channel in self.channels:
            if channel.name == channel_name:
                return channel
        return None

    def get_all_filters(self) -> List[Filter]:
        """Get all filters from all channels."""
        all_filters = []
        for channel in self.channels:
            all_filters.extend(channel.filters)
        return all_filters

    def get_enabled_filters(self) -> List[Filter]:
        """Get all enabled filters from all enabled channels."""
        enabled_filters = []
        for channel in self.channels:
            if channel.enabled:
                enabled_filters.extend(channel.get_enabled_filters())
        return enabled_filters

    def calculate_frequency_response(
        self, frequencies: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate the combined frequency response of all enabled channels.
        Returns (magnitude_db, phase_degrees).
        """
        if not self.channels:
            # Return flat response if no channels
            return np.zeros_like(frequencies), np.zeros_like(frequencies)

        # Calculate individual channel responses
        total_magnitude = np.ones_like(frequencies, dtype=complex)

        for channel in self.channels:
            if channel.enabled:
                magnitude_db, phase_degrees = channel.calculate_frequency_response(
                    frequencies, self.sample_rate
                )
                # Convert back to complex for combination
                magnitude_linear = 10 ** (magnitude_db / 20)
                phase_rad = phase_degrees * np.pi / 180
                channel_response = magnitude_linear * np.exp(1j * phase_rad)
                total_magnitude *= channel_response

        # Convert to magnitude and phase
        magnitude_db = 20 * np.log10(np.abs(total_magnitude))
        phase_degrees = np.angle(total_magnitude) * 180 / np.pi

        return magnitude_db, phase_degrees

    def calculate_biquad_coefficients(self) -> List[dict]:
        """
        Calculate biquad coefficients for all enabled channels.
        Returns a list of dictionaries, each containing the coefficients for one biquad section.
        """
        coefficients = []

        for channel in self.channels:
            if channel.enabled:
                channel_coeffs = channel.calculate_biquad_coefficients()
                # Update sample rate in coefficients
                for coeff in channel_coeffs:
                    coeff["sample_rate"] = self.sample_rate
                coefficients.extend(channel_coeffs)

        return coefficients

    def calculate_full_biquad_coefficients(
        self, max_sections: int, data_type: str
    ) -> List[dict]:
        """
        Calculate biquad coefficients for all enabled channels, then pad with identity
        coefficients to reach the specified maximum number of biquad sections.
        Returns a list of dictionaries with exactly max_sections biquad sections.
        """
        # Get coefficients from actual channels
        used_coefficients = self.calculate_biquad_coefficients()

        # Pad with identity coefficients (no filtering)
        dtype = np.dtype(data_type)
        identity_coeff = {
            "channel_name": "identity",
            "filter_name": "identity",
            "filter_type": "identity",
            "b0": dtype.type(1.0),
            "b1": dtype.type(0.0),
            "b2": dtype.type(0.0),
            "a1": dtype.type(0.0),
            "a2": dtype.type(0.0),
        }

        # Create full coefficient list
        full_coefficients = []

        # Add used coefficients
        for i, coeff in enumerate(used_coefficients):
            # Convert to target data type
            coeff_copy = coeff.copy()
            coeff_copy["b0"] = dtype.type(coeff["b0"])
            coeff_copy["b1"] = dtype.type(coeff["b1"])
            coeff_copy["b2"] = dtype.type(coeff["b2"])
            coeff_copy["a1"] = dtype.type(coeff["a1"])
            coeff_copy["a2"] = dtype.type(coeff["a2"])
            full_coefficients.append(coeff_copy)

        # Pad with identity coefficients
        for i in range(len(used_coefficients), max_sections):
            identity_copy = identity_coeff.copy()
            identity_copy["filter_name"] = f"identity_{i}"
            full_coefficients.append(identity_copy)

        return full_coefficients
