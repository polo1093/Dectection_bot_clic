from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.real_mouse_lab import health_check, interruptible_sleep, pace_click, parse_region


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthetic obvious bot score demo")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--region", required=True, type=parse_region)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--focus-wait", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health_check(args.base_url)
    if args.focus_wait:
        print(f"Starting obvious bot demo in {args.focus_wait:.1f}s...")
        interruptible_sleep(args.focus_wait)

    print("Program: obvious_bot_api")
    print("Synthetic API demo: no real mouse movement or click is performed.")
    print(f"Events={args.count} | rate=0.7/s | region={args.region}")

    base_payload = {
        "n": 30,
        "mean_dt": 0.5,
        "std_dt": 0.0,
        "p90_dt": 0.5,
        "mean_speed": 18000.0,
        "std_speed": 0.0,
        "max_speed": 24000.0,
        "straightness": 1.0,
        "mean_abs_turn": 0.0,
        "trusted_ratio": 0.0,
        "pointer_type": "mouse",
        "webdriver": True,
        "plugins_len": 0,
        "languages_len": 1,
        "hardware_concurrency": 4,
        "max_touch_points": 0,
        "ua_len": 12,
        "botd_bot": True,
        "botd_kind": "synthetic_demo",
        "session_id": "obvious-bot-demo",
        "reason": "obvious_bot_demo",
    }

    for index in range(1, args.count + 1):
        event_started_at = time.monotonic()
        payload = {**base_payload, "n": 30 + index, "reason": f"obvious_bot_demo_{index:02d}"}
        response = requests.post(f"{args.base_url}/api/score", json=payload, timeout=2)
        response.raise_for_status()
        result = response.json()
        print(f"{index:02d} Bot probability: {result['bot_probability'] * 100:.0f}%")
        if index < args.count:
            pace_click(event_started_at)


if __name__ == "__main__":
    main()
