from __future__ import annotations

from typing import Any, Dict, Protocol


class Detector(Protocol):
    name: str

    def score(self, payload: Any) -> Dict[str, Any]:
        ...
