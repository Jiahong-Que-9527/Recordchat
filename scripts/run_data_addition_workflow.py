#!/usr/bin/env python3
"""Run the standardized post-addition workflow for RecordChat data batches."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, cmd: list[str]) -> None:
    print(f"[data-workflow] {name}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run standardized data-addition governance checks and optional ingest."
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run ingest after governance checks pass.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the collection before ingest. Only valid with --ingest.",
    )
    parser.add_argument(
        "--source-dir",
        default=str(ROOT / "data" / "raw"),
        help="Source dir to pass to ingest when --ingest is used.",
    )
    args = parser.parse_args()

    if args.reset and not args.ingest:
        parser.error("--reset requires --ingest")

    run_step(
        "Verifying source governance",
        [sys.executable, str(ROOT / "scripts" / "verify_source_governance.py")],
    )

    if args.ingest:
        ingest_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "ingest_docs.py"),
            "--source-dir",
            args.source_dir,
        ]
        if args.reset:
            ingest_cmd.append("--reset")
        run_step("Running ingest", ingest_cmd)
    else:
        print("[data-workflow] Governance passed. Ingest not requested.")
        print(
            "[data-workflow] Next step: run `python3 scripts/run_data_addition_workflow.py --ingest` "
            "to refresh the live corpus."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
