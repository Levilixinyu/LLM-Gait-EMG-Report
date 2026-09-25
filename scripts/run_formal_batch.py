#!/usr/bin/env python3
"""Prepare/check the formal candidate; live calls require exact-plan approval."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.llm.formal_batch import LIVE_ROOT, RELEASE_CHECKS, recover, run, validate_plan
from src.llm.formal_generation import digest, write_once
from src.llm.formal_release import PACKAGE, build_candidate, package_terminal_run, read
from src.llm.compatibility_check import status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("check")
    sub.add_parser("status")
    live = sub.add_parser("run")
    live.add_argument("--live", action="store_true")
    live.add_argument("--authorization", type=Path, required=True)
    recovery = sub.add_parser("recover")
    recovery.add_argument("decision", type=Path)
    sub.add_parser("package")
    lock = sub.add_parser("lock-review")
    lock.add_argument("rater", choices=["rater1", "rater2"])
    lock.add_argument("workbook", type=Path)
    consensus = sub.add_parser("import-consensus")
    consensus.add_argument("submission", type=Path)
    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps(status(LIVE_ROOT), indent=2))
        return
    if args.command == "prepare":
        if (LIVE_ROOT / "run_manifest.json").exists() or (PACKAGE / "plan.json").exists():
            parser.error("A prepared or started plan cannot be overwritten; use a documented new version")
        plan = build_candidate()
        validate_plan(plan, live=True)
        PACKAGE.mkdir(parents=True, exist_ok=True)
        write_once(PACKAGE / "plan.json", plan)
        write_once(PACKAGE / "authorization_TEMPLATE.json", {
            "approved": False, "scope": plan["scope"], "plan_sha256": digest(plan),
            "budget_limit_usd": plan["budget_limit_usd"], "max_total_attempts": plan["max_total_attempts"],
            "confirmation_source": None, "recorded_by": None, "confirmed_at": None,
            "release_checks": {key: {"passed": False, "evidence_path": None, "evidence_sha256": None}
                               for key in sorted(RELEASE_CHECKS)},
        })
        print(json.dumps({"status": "Candidate prepared; no generation authorized", "slots": len(plan["tasks"]),
                          "plan_sha256": digest(plan), "proposed_budget_usd": plan["budget_limit_usd"]}))
        return
    plan = read(PACKAGE / "plan.json")
    if args.command == "check":
        validate_plan(plan, live=True)
        print(json.dumps({"status": "Exact candidate sources and 105 slots verified", "generation_authorized": False}))
    elif args.command == "run":
        if not args.live:
            parser.error("Paid generation requires --live and separate exact-plan authorization")
        print(json.dumps(run(LIVE_ROOT, plan, mode="live", authorization=read(args.authorization))))
    elif args.command == "recover":
        print(json.dumps(recover(LIVE_ROOT, plan, read(args.decision))))
    elif args.command == "package":
        output = ROOT / "data/rating_packets_formal_v1"
        print(json.dumps(package_terminal_run(LIVE_ROOT, plan, output)))
    elif args.command == "lock-review":
        from src.eval.formal_rating import lock_independent_review
        print(json.dumps(lock_independent_review(ROOT / "data/rating_packets_formal_v1", args.rater, args.workbook)))
    elif args.command == "import-consensus":
        from src.eval.formal_consensus import import_final_consensus
        print(json.dumps(import_final_consensus(ROOT / "data/rating_packets_formal_v1", args.submission)))


if __name__ == "__main__":
    main()
