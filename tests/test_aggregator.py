from __future__ import annotations

from types import SimpleNamespace

from detectors.aggregator import Aggregator, clamp01


class FixedDetector:
    def __init__(self, name: str, score: float, raw: dict | None = None) -> None:
        self.name = name
        self._score = score
        self._raw = raw or {}

    def score(self, payload: object) -> dict:
        return {"score": self._score, "raw": self._raw}


def test_clamp01_bounds_values() -> None:
    assert clamp01(-0.5) == 0.0
    assert clamp01(0.4) == 0.4
    assert clamp01(1.5) == 1.0


def test_aggregator_uses_max_detector_score() -> None:
    aggregator = Aggregator(
        [
            FixedDetector("low", 0.15, {"source": "low"}),
            FixedDetector("high", 0.72, {"source": "high"}),
        ],
        model_name="test_combo",
    )

    result = aggregator.score(SimpleNamespace())

    assert result["bot_probability"] == 0.72
    assert result["raw_score"] == 0.72
    assert result["model"] == "test_combo"
    assert result["signals"]["low"]["score"] == 0.15
    assert result["signals"]["high"]["raw"] == {"source": "high"}


def test_aggregator_clamps_detector_score_above_one() -> None:
    aggregator = Aggregator([FixedDetector("too_high", 2.4)])

    result = aggregator.score(SimpleNamespace())

    assert result["bot_probability"] == 1.0
    assert result["raw_score"] == 1.0


def test_aggregator_handles_empty_detector_list() -> None:
    aggregator = Aggregator([])

    result = aggregator.score(SimpleNamespace())

    assert result["bot_probability"] == 0.0
    assert result["signals"] == {}
