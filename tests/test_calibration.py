"""Unit tests for the two algorithms between logits and decision. These run without weights or images."""
import torch

from api.calibration import AbstentionGate, Calibrator, CalibrationSettings


def test_temperature_one_is_plain_softmax():
    logits = torch.tensor([2.0, 1.0, 0.5, 0.0, -1.0])
    assert torch.allclose(Calibrator(1.0).calibrate(logits), torch.softmax(logits, dim=-1))


def test_higher_temperature_lowers_top_confidence():
    logits = torch.tensor([4.0, 1.0, 0.0, 0.0, 0.0])
    cool = Calibrator(2.0).calibrate(logits).max()
    warm = Calibrator(0.5).calibrate(logits).max()
    assert cool < torch.softmax(logits, dim=-1).max() < warm


def test_probabilities_sum_to_one_after_calibration():
    probabilities = Calibrator(0.9313).calibrate(torch.tensor([1.0, 2.0, 3.0, 0.0, -2.0]))
    assert abs(float(probabilities.sum()) - 1.0) < 1e-6


def test_gate_answers_above_threshold_and_abstains_below():
    gate = AbstentionGate(0.6455)
    confident = gate.decide(torch.tensor([0.05, 0.05, 0.05, 0.80, 0.05]))
    unsure = gate.decide(torch.tensor([0.30, 0.30, 0.20, 0.10, 0.10]))
    assert confident.label == "CMD" and not confident.abstained
    assert unsure.label is None and unsure.abstained and unsure.confidence == 0.3


def test_gate_rejects_impossible_threshold():
    try:
        AbstentionGate(1.5)
    except ValueError:
        return
    raise AssertionError("a threshold above 1 must be rejected")


def test_missing_calibration_file_falls_back_safely(tmp_path):
    settings = CalibrationSettings.load(tmp_path / "missing.json")
    assert settings.temperature == 1.0 and settings.threshold < 1e-6 and "not found" in settings.fitted_on
