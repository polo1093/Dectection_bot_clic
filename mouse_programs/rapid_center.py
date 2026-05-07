from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.real_mouse_lab import RealMouseActor, center, health_check, parse_region


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repeated rapid center clicks")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--region", required=True, type=parse_region)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--focus-wait", type=float, default=3.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health_check(args.base_url)
    actor = RealMouseActor()
    point = center(args.region)
    print(f"Program: rapid_center | clicks={args.count} | point={point}")
    if args.focus_wait:
        print(f"Starting in {args.focus_wait:.1f}s...")
        time.sleep(args.focus_wait)

    for index in range(1, args.count + 1):
        actor.double_click(point, duration=0.08)
        print(f"{index:02d} double-clicked {point}")
        time.sleep(0.1)


if __name__ == "__main__":
    main()
