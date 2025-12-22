from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import joblib

FEATURE_ORDER = [
    "n",
    "mean_dt",
    "std_dt",
    "p90_dt",
    "mean_speed",
    "std_speed",
    "max_speed",
    "straightness",
    "mean_abs_turn",
    "trusted_ratio",
    # pointer_type is handled separately (one-hot-ish) in training script if you want;
    # in this POC we ignore pointer_type in the model and keep it for monitoring.
]

def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))

@dataclass
class Calibration:
    k: float = 6.0
    offset: float = 0.0

class BotRiskModel:
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.model_path = models_dir / "isoforest.joblib"
        self.calib_path = models_dir / "calibration.json"
        self.pipeline = None
        self.calib = Calibration()
        self._load_if_exists()

    @property
    def is_loaded(self) -> bool:
        return self.pipeline is not None

    def _load_if_exists(self) -> None:
        if self.model_path.exists():
            self.pipeline = joblib.load(self.model_path)
        if self.calib_path.exists():
            data = json.loads(self.calib_path.read_text(encoding="utf-8"))
            self.calib = Calibration(**data)

    def _vectorize(self, features: Dict[str, Any]) -> np.ndarray:
        x = []
        for k in FEATURE_ORDER:
            x.append(float(features.get(k, 0.0)))
        return np.array(x, dtype=np.float64).reshape(1, -1)

    def score(self, features: Dict[str, Any]) -> Tuple[float, float, Dict[str, Any]]:
        # raw_score: higher = more "outlier" (more bot-like)
        x = self._vectorize(features)

        if self.pipeline is None:
            # Fallback heuristic (no model yet):
            # - extremely low dt variance + very high straightness are suspicious
            mean_dt = float(features.get("mean_dt", 0.0))
            std_dt = float(features.get("std_dt", 0.0))
            straight = float(features.get("straightness", 0.0))
            max_speed = float(features.get("max_speed", 0.0))

            raw = 0.0
            raw += 2.0 * max(0.0, (0.010 - std_dt))          # trop "métronomique"
            raw += 1.5 * max(0.0, (straight - 0.98))         # trop rectiligne
            raw += 0.5 * max(0.0, (max_speed - 5000.0) / 5000.0)  # sauts rapides
            p = _sigmoid(raw - 1.0)
            return p, raw, {"model": "heuristic"}

        # scikit-learn: decision_function higher = inlier, lower = outlier
        inlier_score = float(self.pipeline.decision_function(x)[0])
        raw = -inlier_score  # higher = more anomalous

        # calibration -> probability
        z = self.calib.k * (raw - self.calib.offset)
        p = _sigmoid(z)
        return float(p), raw, {"model": "IsolationForest+calibration"}

