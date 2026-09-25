#!/usr/bin/env python3
"""Separate full-length synthetic check: prepare/check by default, never implicit live calls."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.full_length_check import PACKAGE, LIVE_ROOT, build_plan
from src.llm.formal_batch import run, recover, validate_plan, terminal_slots
from src.llm.formal_generation import digest, write_once
from src.llm.compatibility_check import status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "check", "status", "results"):
        sub.add_parser(command)
    live = sub.add_parser("run")
    live.add_argument("--live", action="store_true")
    live.add_argument("--authorization", type=Path, required=True)
    recovery = sub.add_parser("recover")
    recovery.add_argument("decision", type=Path)
    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps(status(LIVE_ROOT), indent=2))
        return
    if args.command == "prepare":
        if (PACKAGE / "plan.json").exists() or (LIVE_ROOT / "run_manifest.json").exists():
            parser.error("Do not overwrite a prepared or started check")
        plan = build_plan()
        validate_plan(plan, live=True)
        PACKAGE.mkdir(parents=True, exist_ok=True)
        write_once(PACKAGE / "plan.json", plan)
        (PACKAGE / "synthetic_system_prompt.txt").write_text(plan["tasks"][0]["system_prompt"])
        (PACKAGE / "synthetic_user_prompt.txt").write_text(plan["tasks"][0]["user_prompt"])
        write_once(PACKAGE / "authorization_TEMPLATE.json", {
            "approved": False, "scope": plan["scope"], "plan_sha256": digest(plan),
            "budget_limit_usd": 4.0, "max_total_attempts": 9,
            "confirmation_source": None, "recorded_by": None, "confirmed_at": None})
        print(json.dumps({"status": "Synthetic plan prepared, not authorized", "input_bytes": plan["input_utf8_bytes"],
                          "intended_responses": 3, "max_attempts": 9, "budget_limit_usd": 4.0}))
        return
    plan = json.loads((PACKAGE / "plan.json").read_text())
    if args.command == "check":
        validate_plan(plan, live=True)
        print(json.dumps({"status": "Exact synthetic plan and sources verified", "live_authorized": False}))
    elif args.command == "run":
        if not args.live:
            parser.error("Explicit --live and exact-plan authorization are required")
        print(json.dumps(run(LIVE_ROOT, plan, mode="live", authorization=json.loads(args.authorization.read_text()))))
    elif args.command == "recover":
        print(json.dumps(recover(LIVE_ROOT, plan, json.loads(args.decision.read_text()))))
    elif args.command == "results":
        slots = terminal_slots(LIVE_ROOT, plan)
        print(json.dumps([{"slot_id": s["slot_id"], "state": s["terminal_status"], "words": len((s["report_text"] or "").split()),
                          "truncation": s["truncation"], "normal_stream_completion": s["normal_stream_completion"],
                          "metadata": s["metadata"]} for s in slots], indent=2))


if __name__ == "__main__":
    main()
