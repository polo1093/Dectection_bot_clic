from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from model import BotRiskModel
from storage import append_row_csv

APP_DIR = Path(__file__).resolve().parent
MODELS_DIR = APP_DIR / "models"
DATA_DIR = APP_DIR / "data"

app = FastAPI(title="Bot risk (browser game) — POC")

# Serve static assets (index + JS)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

# Load model (if present)
model = BotRiskModel(models_dir=MODELS_DIR)

class FeaturePayload(BaseModel):
    # Minimal feature set (extensible)
    n: int = Field(..., ge=1)

    mean_dt: float
    std_dt: float
    p90_dt: float

    mean_speed: float
    std_speed: float
    max_speed: float

    straightness: float  # displacement / path_length in [0,1]
    mean_abs_turn: float # average abs turning angle (rad)

    trusted_ratio: float = Field(..., ge=0.0, le=1.0)
    pointer_type: Optional[str] = None  # "mouse" | "touch" | "pen"

class ScoreResponse(BaseModel):
    bot_probability: float
    model: str
    raw_score: float

@app.get("/", response_class=HTMLResponse)
def index() -> Any:
    html = (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "model_loaded": model.is_loaded}

@app.post("/api/score", response_model=ScoreResponse)
def score(payload: FeaturePayload) -> Any:
    p, raw, meta = model.score(payload.model_dump())
    return {"bot_probability": p, "model": meta["model"], "raw_score": raw}

@app.post("/api/collect/human")
def collect_human(payload: FeaturePayload) -> Dict[str, Any]:
    row = payload.model_dump()
    row["label"] = "human"
    append_row_csv(DATA_DIR / "human_samples.csv", row)
    return {"ok": True}

