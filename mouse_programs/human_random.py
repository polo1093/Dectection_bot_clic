from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.real_mouse_lab import RealMouseActor, health_check, parse_region, run_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Human-like random mouse program")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--region", required=True, type=parse_region)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--focus-wait", type=float, default=3.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health_check(args.base_url)
    print(f"Program: human_random | clicks={args.count} | region={args.region}")
    if args.focus_wait:
        print(f"Starting in {args.focus_wait:.1f}s...")
        time.sleep(args.focus_wait)

    run_profile(
        mode="human",
        actor=RealMouseActor(),
        region=args.region,
        count=args.count,
        base_url=args.base_url,
        session_id=None,
        min_delay=0.25,
        max_delay=0.8,
    )


if __name__ == "__main__":
    main()
