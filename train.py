from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from model import FEATURE_ORDER

APP_DIR = Path(__file__).resolve().parent
DATA = APP_DIR / "data" / "human_samples.csv"
MODELS_DIR = APP_DIR / "models"
MODEL_PATH = MODELS_DIR / "isoforest.joblib"
CALIB_PATH = MODELS_DIR / "calibration.json"

def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"Missing {DATA}. Collect some samples first via the UI.")

    df = pd.read_csv(DATA)

    # Keep only human label (this POC is "train-on-humans" anomaly detection)
    if "label" in df.columns:
        df = df[df["label"] == "human"]

    # Basic hygiene
    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    if len(df) < 50:
        raise SystemExit(f"Need more samples (got {len(df)}). Aim for 200+.")

    X = df[FEATURE_ORDER].astype(float).to_numpy()

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("isof", IsolationForest(
            n_estimators=300,
            contamination=0.03,  # expected outlier fraction (tune)
            random_state=42,
        )),
    ])

    pipe.fit(X)

    # Calibration: map anomaly score -> probability
    # decision_function higher=inlier; we use raw = -decision_function
    inlier_scores = pipe.decision_function(X)
    raw = -inlier_scores

    # offset at high quantile of human raw scores (so most humans => low probability)
    offset = float(np.quantile(raw, 0.95))
    # scale to spread probabilities reasonably
    spread = float(np.quantile(raw, 0.99) - np.quantile(raw, 0.50))
    spread = max(spread, 1e-6)
    k = float(6.0 / spread)  # heuristic

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    CALIB_PATH.write_text(json.dumps({"k": k, "offset": offset}, indent=2), encoding="utf-8")

    print("Saved:", MODEL_PATH)
    print("Saved:", CALIB_PATH)
    print(f"Samples used: {len(df)}")
    print(f"Calibration: k={k:.4f}, offset={offset:.6f}")

if __name__ == "__main__":
    main()
