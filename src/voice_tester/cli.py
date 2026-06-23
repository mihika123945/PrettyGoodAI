from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import uvicorn

from voice_tester.analyzer import analyze_run, compile_bug_report
from voice_tester.caller import fetch_recording, hangup_call, place_call
from voice_tester.config import Settings
from voice_tester.scenarios import SCENARIOS, get_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pretty Good AI voice testing harness")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run the SignalWire webhook and media server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", default=8000, type=int)

    sub.add_parser("scenarios", help="List included patient scenarios")

    call = sub.add_parser("call", help="Place one assessment call")
    call.add_argument("scenario_id")
    call.add_argument("--dry-run", action="store_true")

    batch = sub.add_parser("batch", help="Place a sequence of assessment calls")
    batch.add_argument("--count", type=int, default=10, choices=range(1, len(SCENARIOS) + 1))
    batch.add_argument("--delay", type=int, default=20, help="Seconds between call creation")
    batch.add_argument("--dry-run", action="store_true")

    analyze = sub.add_parser("analyze", help="Analyze one completed transcript")
    analyze.add_argument("run_id")

    hangup = sub.add_parser("hangup", help="End a SignalWire call for a run")
    hangup.add_argument("run_id")

    recording = sub.add_parser("recording", help="Fetch the SignalWire MP3 recording for a run")
    recording.add_argument("run_id")

    report = sub.add_parser("report", help="Compile analyzed calls into BUG_REPORT.md")
    report.add_argument("--output", default="BUG_REPORT.md")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.command == "serve":
        settings.require_call_credentials()
        uvicorn.run(
            "voice_tester.server:create_app",
            host=args.host,
            port=args.port,
            factory=True,
            reload=False,
        )
    elif args.command == "scenarios":
        for scenario in SCENARIOS:
            print(f"{scenario.id}: {scenario.title}")
    elif args.command == "call":
        result = place_call(settings, get_scenario(args.scenario_id), dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.command == "batch":
        for index, scenario in enumerate(SCENARIOS[: args.count]):
            result = place_call(settings, scenario, dry_run=args.dry_run)
            print(json.dumps(result, indent=2))
            if index + 1 < args.count and not args.dry_run:
                time.sleep(args.delay)
    elif args.command == "analyze":
        print(analyze_run(settings, args.run_id))
    elif args.command == "hangup":
        print(json.dumps(hangup_call(settings, args.run_id), indent=2))
    elif args.command == "recording":
        print(fetch_recording(settings, args.run_id))
    elif args.command == "report":
        print(compile_bug_report(settings.data_dir, destination=Path(args.output)))
