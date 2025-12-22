from __future__ import annotations

from typing import Any, Dict

from .base import Detector


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


class HeuristicMouseV1(Detector):
    name = "mouse_heuristic_v1"

    def score(self, payload: Any) -> Dict[str, Any]:
        """
        Risk score heuristique:
        - combine "automation flags" + "mouse dynamics anomalies"
        - sortie: probability in [0,1]
        """
        risk = 0.0

        # 1) Signaux d’automatisation (forts)
        if payload.webdriver is True:
            risk += 0.55  # très suspect

        # plugins=0 sur certains contextes (headless/locked-down). Signal moyen.
        if payload.plugins_len is not None and payload.plugins_len == 0:
            risk += 0.10

        # langues vides/1 seule: parfois bot/containers. Signal faible-moyen.
        if payload.languages_len is not None and payload.languages_len <= 1:
            risk += 0.08

        # 2) Cinématique souris (sans modèle, on score des "patterns improbables")
        # Très “métronomique” (faible variance de dt)
        if payload.std_dt < 2.0:         # ms (après clamp côté JS)
            risk += 0.18
        elif payload.std_dt < 5.0:
            risk += 0.10

        # Trajectoire trop rectiligne de façon répétée
        if payload.straightness > 0.995:
            risk += 0.16
        elif payload.straightness > 0.985:
            risk += 0.10

        # Peu de changements de direction (faible mean_abs_turn)
        if payload.mean_abs_turn < 0.03:
            risk += 0.12
        elif payload.mean_abs_turn < 0.06:
            risk += 0.06

        # Vitesse max “sauts” très élevés (téléportation du curseur / injection)
        if payload.max_speed > 12000.0:
            risk += 0.20
        elif payload.max_speed > 8000.0:
            risk += 0.12

        # Si beaucoup d'événements non trusted (dispatch JS), suspect.
        # NB: pas fiable à 100%, donc poids modéré.
        if payload.trusted_ratio < 0.95:
            risk += 0.10
        if payload.trusted_ratio < 0.80:
            risk += 0.18

        # 3) Qualité de fenêtre (n trop petit => score moins “confiant”)
        # On pénalise légèrement (on évite d'accuser à partir de 5 points…)
        if payload.n < 25:
            risk *= 0.75

        # 4) Normalisation / probabilité
        # Ici: risque brut déjà calibré "à la main". On clamp.
        prob = clamp01(risk)

        return {
            "score": prob,
            "raw": {
                "risk": risk,
            },
        }
