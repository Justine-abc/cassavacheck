"""Calibration and abstention: the two steps between raw logits and a decision. Both read frozen values; nothing is fitted here."""
import json
from dataclasses import dataclass
from pathlib import Path

import torch

from api.config import CLASS_NAMES


@dataclass(frozen=True)
class Decision:
    """What the system tells the user. abstained=True means no label is given."""
    label: str | None
    confidence: float
    probabilities: dict[str, float]
    abstained: bool


class Calibrator:
    """Temperature scaling (Guo et al., 2017): divide the logits by one number fitted on validation data, then softmax.
    A temperature above 1 cools an over-confident model; below 1 warms an under-confident one."""

    def __init__(self, temperature: float):
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        self.temperature = float(temperature)

    def calibrate(self, logits: torch.Tensor) -> torch.Tensor:
        return torch.softmax(logits / self.temperature, dim=-1)


class AbstentionGate:
    """Selective classification (Geifman & El-Yaniv, 2017): answer only when the top calibrated probability clears a threshold
    that was set on validation data for a target coverage."""

    def __init__(self, threshold: float):
        if not 0.0 < threshold < 1.0:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = float(threshold)

    def decide(self, probabilities: torch.Tensor) -> Decision:
        confidence, index = probabilities.max(dim=-1)
        confidence = float(confidence)
        as_dict = {name: round(float(value), 4) for name, value in zip(CLASS_NAMES, probabilities.tolist())}
        if confidence < self.threshold:
            return Decision(label=None, confidence=round(confidence, 4), probabilities=as_dict, abstained=True)
        return Decision(label=CLASS_NAMES[int(index)], confidence=round(confidence, 4), probabilities=as_dict, abstained=False)


@dataclass(frozen=True)
class CalibrationSettings:
    temperature: float
    threshold: float
    target_coverage: float
    fitted_on: str

    @classmethod
    def load(cls, path: Path) -> "CalibrationSettings":
        """Read the frozen values written by notebook 04. If the file is missing, fall back to an uncalibrated, never-abstaining
        configuration and say so, so a developer notices rather than silently getting different behaviour."""
        if not path.exists():
            return cls(temperature=1.0, threshold=1e-9, target_coverage=1.0, fitted_on="none: calibration.json not found")
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(temperature=float(raw["temperature"]), threshold=float(raw["threshold"]),
                   target_coverage=float(raw.get("target_coverage", 0.8)), fitted_on=str(raw.get("fitted_on", "unknown")))
