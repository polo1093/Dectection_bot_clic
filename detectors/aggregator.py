from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .base import Detector


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


class Aggregator:
    def __init__(self, detectors: Iterable[Detector], model_name: str = "combo_v1") -> None:
        self.detectors: List[Detector] = list(detectors)
        self.model_name = model_name

    def score(self, payload: Any) -> Dict[str, Any]:
        signals: Dict[str, Dict[str, Any]] = {}
        scores: List[float] = []

        for detector in self.detectors:
            result = detector.score(payload)
            score = float(result.get("score", 0.0))
            scores.append(score)
            signals[detector.name] = {
                "score": score,
                "raw": result.get("raw", {}),
            }

        # combo_v1: max of signals to keep a strong detector as a hard signal.
        global_score = clamp01(max(scores) if scores else 0.0)

        return {
            "bot_probability": global_score,
            "model": self.model_name,
            "raw_score": global_score,
            "signals": signals,
        }
