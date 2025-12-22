from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


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


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def score_heuristic(p: FeaturePayload) -> Dict[str, float]:
    """
    Risk score heuristique:
    - combine "automation flags" + "mouse dynamics anomalies"
    - sortie: probability in [0,1]
    """
    risk = 0.0

    # 1) Signaux d’automatisation (forts)
    if p.webdriver is True:
        risk += 0.55  # très suspect

    # plugins=0 sur certains contextes (headless/locked-down). Signal moyen.
    if p.plugins_len is not None and p.plugins_len == 0:
        risk += 0.10

    # langues vides/1 seule: parfois bot/containers. Signal faible-moyen.
    if p.languages_len is not None and p.languages_len <= 1:
        risk += 0.08

    # 2) Cinématique souris (sans modèle, on score des "patterns improbables")
    # Très “métronomique” (faible variance de dt)
    if p.std_dt < 2.0:         # ms (après clamp côté JS)
        risk += 0.18
    elif p.std_dt < 5.0:
        risk += 0.10

    # Trajectoire trop rectiligne de façon répétée
    if p.straightness > 0.995:
        risk += 0.16
    elif p.straightness > 0.985:
        risk += 0.10

    # Peu de changements de direction (faible mean_abs_turn)
    if p.mean_abs_turn < 0.03:
        risk += 0.12
    elif p.mean_abs_turn < 0.06:
        risk += 0.06

    # Vitesse max “sauts” très élevés (téléportation du curseur / injection)
    if p.max_speed > 12000.0:
        risk += 0.20
    elif p.max_speed > 8000.0:
        risk += 0.12

    # Si beaucoup d'événements non trusted (dispatch JS), suspect.
    # NB: pas fiable à 100%, donc poids modéré.
    if p.trusted_ratio < 0.95:
        risk += 0.10
    if p.trusted_ratio < 0.80:
        risk += 0.18

    # 3) Qualité de fenêtre (n trop petit => score moins “confiant”)
    # On pénalise légèrement (on évite d'accuser à partir de 5 points…)
    if p.n < 25:
        risk *= 0.75

    # 4) Normalisation / probabilité
    # Ici: risque brut déjà calibré "à la main". On clamp.
    prob = clamp01(risk)

    return {"bot_probability": prob, "raw_score": risk}


@app.get("/", response_class=HTMLResponse)
def index() -> Any:
    html = (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@app.post("/api/score")
def score(payload: FeaturePayload) -> Dict[str, Any]:
    out = score_heuristic(payload)
    return {
        "bot_probability": out["bot_probability"],
        "model": "heuristic_v1",
        "raw_score": out["raw_score"],
    }
