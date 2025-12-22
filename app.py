from __future__ import annotations

from collections import deque
from pathlib import Path
import threading
import time
from typing import Any, Deque, Dict, Optional

from fastapi import FastAPI
from fastapi import Query
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

    session_id: Optional[str] = None
    reason: Optional[str] = None


aggregator = Aggregator([HeuristicMouseV1(), BotdV2()])
telemetry_events: Deque[Dict[str, Any]] = deque(maxlen=200)
telemetry_lock = threading.Lock()


@app.get("/", response_class=HTMLResponse)
def index() -> Any:
    html = (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@app.post("/api/score")
def score(payload: FeaturePayload) -> Dict[str, Any]:
    result = aggregator.score(payload)
    session_id = payload.session_id or "default"
    event = {
        "ts": time.time(),
        "session_id": session_id,
        "reason": payload.reason,
        "bot_probability": result["bot_probability"],
        "model": result["model"],
        "raw_score": result["raw_score"],
        "signals": result.get("signals"),
    }
    with telemetry_lock:
        telemetry_events.append(event)
    return result


@app.get("/api/telemetry")
def telemetry(
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
) -> list[Dict[str, Any]]:
    with telemetry_lock:
        events = list(telemetry_events)
    if session_id:
        events = [event for event in events if event.get("session_id") == session_id]
    return events[-limit:]
