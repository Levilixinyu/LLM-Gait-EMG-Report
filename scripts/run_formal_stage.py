#!/usr/bin/env python3
"""Run only the explicitly authorized formal stage, then stop."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.formal_stages import FULL_PLAN, PACKAGE, LIVE_ROOT, run_stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, required=True, choices=(1, 2, 3))
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("Explicit --live and an existing bounded authorization are required")
    folder = PACKAGE / f"stage_{args.stage:02d}"
    read = lambda p: json.loads(p.read_text())
    result = run_stage(LIVE_ROOT, read(FULL_PLAN), read(folder / "plan.json"),
                       read(folder / "authorization.json"),
                       progress=lambda row: print(json.dumps(row), flush=True))
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
