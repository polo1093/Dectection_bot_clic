from __future__ import annotations

from typing import Any, Dict

from .base import Detector


class BotdV2(Detector):
    name = "botd_v2"

    def score(self, payload: Any) -> Dict[str, Any]:
        if payload.botd_bot is True:
            score = 0.95
        elif payload.botd_bot is False:
            score = 0.0
        else:
            score = 0.0

        return {
            "score": score,
            "raw": {
                "bot": payload.botd_bot,
                "kind": payload.botd_kind,
            },
        }
