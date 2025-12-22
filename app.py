from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from detectors.aggregator import Aggregator
from detectors.botd_v2 import BotdV2
from detectors.heuristic_mouse_v1 import HeuristicMouseV1

APP_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Bot risk (browser game) — heuristic scoring")

app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")


class FeaturePayload(BaseModel):
    # movement/click features
    n: int = Field(..., ge=1)
    mean_dt: float
    std_dt: float
    p90_dt: float
    mean_speed: float
    std_speed: float
    max_speed: float
    straightness: float = Field(..., ge=0.0, le=1.0)
    mean_abs_turn: float
    trusted_ratio: float = Field(..., ge=0.0, le=1.0)
    pointer_type: Optional[str] = None

    # minimal “automation / environment” signals (no training, just heuristics)
    webdriver: Optional[bool] = None
    plugins_len: Optional[int] = None
    languages_len: Optional[int] = None
    hardware_concurrency: Optional[int] = None
    max_touch_points: Optional[int] = None
    ua_len: Optional[int] = None

    botd_bot: Optional[bool] = None
    botd_kind: Optional[str] = None


aggregator = Aggregator([HeuristicMouseV1(), BotdV2()])


@app.get("/", response_class=HTMLResponse)
def index() -> Any:
    html = (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@app.post("/api/score")
def score(payload: FeaturePayload) -> Dict[str, Any]:
    return aggregator.score(payload)
