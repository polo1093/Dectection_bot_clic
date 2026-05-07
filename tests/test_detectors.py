from __future__ import annotations

from types import SimpleNamespace

from detectors.botd_v2 import BotdV2
from detectors.heuristic_mouse_v1 import HeuristicMouseV1


def payload(**overrides: object) -> SimpleNamespace:
    defaults = {
        "webdriver": False,
        "plugins_len": 3,
        "languages_len": 2,
        "std_dt": 20.0,
        "straightness": 0.8,
        "mean_abs_turn": 0.5,
        "max_speed": 1200.0,
        "trusted_ratio": 1.0,
        "n": 40,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_mouse_heuristic_keeps_normal_payload_low_risk() -> None:
    result = HeuristicMouseV1().score(payload())

    assert result["score"] == 0.0
    assert result["raw"]["risk"] == 0.0


def test_mouse_heuristic_scores_obvious_automation_signals() -> None:
    result = HeuristicMouseV1().score(
        payload(
            webdriver=True,
            plugins_len=0,
            languages_len=1,
            std_dt=1.0,
            straightness=0.999,
            mean_abs_turn=0.01,
            max_speed=14000.0,
            trusted_ratio=0.70,
        )
    )

    assert result["score"] == 1.0
    assert result["raw"]["risk"] > 1.0


def test_mouse_heuristic_reduces_confidence_for_small_window() -> None:
    large_window = HeuristicMouseV1().score(payload(std_dt=1.0, n=40))
    small_window = HeuristicMouseV1().score(payload(std_dt=1.0, n=10))

    assert large_window["score"] == 0.18
    assert small_window["score"] == 0.135


def test_botd_scores_detected_bot_as_high_risk() -> None:
    detector = BotdV2()

    result = detector.score(SimpleNamespace(botd_bot=True, botd_kind="webdriver"))

    assert result["score"] == 0.95
    assert result["raw"] == {"bot": True, "kind": "webdriver"}


def test_botd_scores_human_or_unknown_as_zero() -> None:
    detector = BotdV2()

    human = detector.score(SimpleNamespace(botd_bot=False, botd_kind=None))
    unknown = detector.score(SimpleNamespace(botd_bot=None, botd_kind=None))

    assert human["score"] == 0.0
    assert unknown["score"] == 0.0
