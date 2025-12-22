#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import time
from pathlib import Path
from typing import Optional, Sequence, Tuple

import requests

try:
    from human_mouse import MouseController
except ImportError as exc:
    raise SystemExit(
        "human-mouse is required. Install it with: pip install human-mouse"
    ) from exc


def parse_region(value: str) -> Tuple[int, int, int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("REGION must be in the format x1,y1,x2,y2")
    x1, y1, x2, y2 = (int(part) for part in parts)
    if x2 <= x1 or y2 <= y1:
        raise ValueError("REGION requires x2 > x1 and y2 > y1")
    return x1, y1, x2, y2


def read_session_id(path: Path) -> str:
    session_id = path.read_text(encoding="utf-8").strip()
    if not session_id:
        raise ValueError(f"Session id file is empty: {path}")
    return session_id


def fetch_latest_event(
    base_url: str, session_id: Optional[str], limit: int
) -> Optional[dict]:
    params = {"limit": limit}
    if session_id:
        params["session_id"] = session_id
    response = requests.get(f"{base_url}/api/telemetry", params=params, timeout=2)
    response.raise_for_status()
    events = response.json()
    if not isinstance(events, list):
        raise ValueError("Telemetry response must be a JSON list")
    return events[-1] if events else None


def health_check(base_url: str) -> None:
    response = requests.get(f"{base_url}/api/health", timeout=2)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise SystemExit("Health check failed: /api/health returned ok=false")


def random_point(region: Sequence[int]) -> Tuple[int, int]:
    x1, y1, x2, y2 = region
    x = random.randint(x1, x2)
    y = random.randint(y1, y2)
    return x, y


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Human mouse bot-risk test tool")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--session-id-file", type=Path, default=None)
    parser.add_argument("--region", required=True, help="x1,y1,x2,y2 screen coords")
    parser.add_argument("--n-clicks", type=int, default=5)
    parser.add_argument("--min-delay", type=float, default=0.6)
    parser.add_argument("--max-delay", type=float, default=1.4)
    parser.add_argument("--post-wait-min", type=float, default=0.2)
    parser.add_argument("--post-wait-max", type=float, default=0.5)
    parser.add_argument("--min-speed-factor", type=float, default=0.7)
    parser.add_argument("--max-speed-factor", type=float, default=1.3)
    parser.add_argument("--focus-wait", type=float, default=3.0)
    parser.add_argument("--skip-health-check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    region = parse_region(args.region)

    session_id = args.session_id
    if args.session_id_file:
        session_id = read_session_id(args.session_id_file)

    if not args.skip_health_check:
        health_check(args.base_url)

    print("Focus the browser window now...")
    time.sleep(args.focus_wait)

    mouse = MouseController(always_zigzag=True)
    scores = []

    for idx in range(1, args.n_clicks + 1):
        x, y = random_point(region)
        speed_factor = random.uniform(args.min_speed_factor, args.max_speed_factor)
        mouse.move(x, y, speed_factor=speed_factor)
        time.sleep(random.uniform(0.05, 0.2))
        mouse.perform_click()
        time.sleep(random.uniform(args.post_wait_min, args.post_wait_max))

        event = fetch_latest_event(args.base_url, session_id, limit=5)
        if event:
            scores.append(event["bot_probability"])
            print(
                f"{idx}/{args.n_clicks} bot_probability={event['bot_probability']:.3f} "
                f"model={event['model']} raw={event['raw_score']:.3f} "
                f"reason={event.get('reason')} session_id={event.get('session_id')}"
            )
        else:
            print(f"{idx}/{args.n_clicks} no telemetry event yet")

        time.sleep(random.uniform(args.min_delay, args.max_delay))

    if scores:
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        print(
            f"Summary: scores={len(scores)} avg={avg_score:.3f} max={max_score:.3f}"
        )
    else:
        print("Summary: no scores received")


if __name__ == "__main__":
    main()
