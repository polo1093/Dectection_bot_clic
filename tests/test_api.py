from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with app_module.telemetry_lock:
        app_module.telemetry_events.clear()
    with TestClient(app_module.app) as test_client:
        yield test_client
    with app_module.telemetry_lock:
        app_module.telemetry_events.clear()


def score_payload(**overrides: object) -> dict:
    payload = {
        "n": 40,
        "mean_dt": 16.0,
        "std_dt": 18.0,
        "p90_dt": 30.0,
        "mean_speed": 800.0,
        "std_speed": 120.0,
        "max_speed": 1600.0,
        "straightness": 0.75,
        "mean_abs_turn": 0.4,
        "trusted_ratio": 1.0,
        "pointer_type": "mouse",
        "webdriver": False,
        "plugins_len": 3,
        "languages_len": 2,
        "hardware_concurrency": 8,
        "max_touch_points": 0,
        "ua_len": 100,
        "botd_bot": False,
        "botd_kind": None,
        "session_id": "session-a",
        "reason": "pytest",
    }
    payload.update(overrides)
    return payload


def test_healthcheck(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_index_serves_page(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Bot Risk Game" in response.text


def test_score_returns_signals_and_stores_telemetry(client: TestClient) -> None:
    response = client.post("/api/score", json=score_payload(std_dt=1.0))

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "combo_v1"
    assert body["bot_probability"] == 0.18
    assert set(body["signals"]) == {"mouse_heuristic_v1", "botd_v2"}

    telemetry = client.get("/api/telemetry", params={"session_id": "session-a"})
    assert telemetry.status_code == 200
    events = telemetry.json()
    assert len(events) == 1
    assert events[0]["reason"] == "pytest"
    assert events[0]["bot_probability"] == 0.18


def test_telemetry_filters_by_session_and_limit(client: TestClient) -> None:
    client.post("/api/score", json=score_payload(session_id="a", reason="first"))
    client.post("/api/score", json=score_payload(session_id="b", reason="second"))
    client.post("/api/score", json=score_payload(session_id="a", reason="third"))

    response = client.get("/api/telemetry", params={"session_id": "a", "limit": 1})

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["session_id"] == "a"
    assert events[0]["reason"] == "third"


def test_score_rejects_invalid_payload(client: TestClient) -> None:
    response = client.post(
        "/api/score",
        json=score_payload(n=0, straightness=1.5, trusted_ratio=-0.1),
    )

    assert response.status_code == 422
