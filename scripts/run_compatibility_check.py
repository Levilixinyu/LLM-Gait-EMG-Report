#!/usr/bin/env python3
"""Prepare, inspect, execute or recover the fixed synthetic check.

Default: read-only validation. Real HTTP requires `run --live` plus an approved
authorization record matching the exact plan. No participant inputs accepted.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.compatibility_check import PACKAGE, LIVE_ROOT, build_plan, digest, recovery, run_check, status, technical_results, validate_plan
from src.llm.formal_generation import IntegrityError


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=["prepare", "check", "status", "run", "recover"], default="check")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--decision", type=Path, help="Local JSON technical recovery decision")
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            PACKAGE.mkdir(parents=True, exist_ok=True)
            if (LIVE_ROOT / "run_manifest.json").exists():
                raise IntegrityError("A live check has already started; preserve its plan and resume the same run")
            authorization_path = PACKAGE / "authorization.json"
            if authorization_path.exists() and json.loads(authorization_path.read_text()).get("approved"):
                raise IntegrityError("Approved check cannot be silently re-prepared")
            plan = build_plan()
            dump(PACKAGE / "plan.json", plan)
            dump(authorization_path, {"approved": False, "scope": plan["scope"], "plan_sha256": digest(plan),
                "max_total_dispatches": 9, "budget_limit_usd": 3.0,
                "confirmation_source": "", "recorded_by": "", "confirmed_at": ""})
            print(json.dumps({"status": "prepared_without_calls", "plan_sha256": digest(plan),
                "intended_responses": 3, "max_dispatches": 9, "estimated_maximum_usd": plan["estimated_maximum_usd"]}))
            return
        if args.action == "status":
            print(json.dumps(status(LIVE_ROOT)))
            return
        plan = json.loads((PACKAGE / "plan.json").read_text())
        validate_plan(plan)
        if args.action == "check":
            auth = json.loads((PACKAGE / "authorization.json").read_text())
            print(json.dumps({"status": "plan_valid", "plan_sha256": digest(plan),
                "authorization_record_approved": auth.get("approved") is True, "model_calls_in_this_command": 0}))
        elif args.action == "run":
            if not args.live:
                raise IntegrityError("Live mode requires explicit --live and a specific authorization record")
            auth = json.loads((PACKAGE / "authorization.json").read_text())
            result = run_check(LIVE_ROOT, plan, mode="live", authorization=auth)
            summary = {"run_status": result["status"], **status(LIVE_ROOT)}
            dump(LIVE_ROOT / "last_summary.json", summary)
            dump(LIVE_ROOT / "technical_results.json", technical_results(LIVE_ROOT))
            print(json.dumps(summary))
        elif args.action == "recover":
            if args.decision is None:
                raise IntegrityError("A documented recovery decision file is required")
            path = args.decision.resolve()
            if not path.is_relative_to(ROOT) or path.is_relative_to(ROOT / "data/raw"):
                raise IntegrityError("Recovery evidence must be in the active project evidence area")
            result = recovery(LIVE_ROOT, plan, json.loads(path.read_text()))
            print(json.dumps({"state": result["state"], "slot_id": result["slot_id"], "model_calls_in_this_command": 0}))
    except (IntegrityError, FileNotFoundError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
