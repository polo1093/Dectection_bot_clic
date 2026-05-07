from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.real_mouse_lab import (
    RealMouseActor,
    check_emergency_stop,
    grid_points,
    health_check,
    interruptible_sleep,
    pace_click,
    parse_region,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fast teleport grid mouse program")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--region", required=True, type=parse_region)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--focus-wait", type=float, default=3.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health_check(args.base_url)
    actor = RealMouseActor()
    print(f"Program: teleport_grid | clicks={args.count} | region={args.region}")
    if args.focus_wait:
        print(f"Starting in {args.focus_wait:.1f}s...")
        interruptible_sleep(args.focus_wait)

    points = grid_points(args.region, args.count)
    for index, point in enumerate(points, start=1):
        click_started_at = time.monotonic()
        check_emergency_stop()
        actor.teleport_click(point)
        print(f"{index:02d} clicked {point}")
        if index < len(points):
            pace_click(click_started_at)


if __name__ == "__main__":
    main()
