"""Publish a complete validated artifact pair to an explicit new directory."""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from assertion_engine.artifacts import canonical_bytes, decode_json, validate_pair
from assertion_engine.simulator.config import load_config
from assertion_engine.simulator.scenario import generate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="assertion-sim")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("generate", help="generate normal-flight artifacts")
    command.add_argument("--scenario", required=True)
    command.add_argument("--output", required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return error.code
    if not args.scenario or not args.output:
        print("--scenario and --output must name explicit paths", file=sys.stderr)
        return 2
    output = Path(args.output)
    try:
        source = load_config(args.scenario)
    except ValueError as error:
        print(f"invalid scenario {args.scenario}: {error}", file=sys.stderr)
        return 2
    if os.path.lexists(output):
        print(f"output {output}: target already exists", file=sys.stderr)
        return 2
    try:
        telemetry, truth = generate(source)
        telemetry_bytes = canonical_bytes(telemetry)
        truth_bytes = canonical_bytes(truth)
        # Validate the complete published representation, including source
        # precision, before creating even the first missing parent.
        validate_pair(decode_json(telemetry_bytes), decode_json(truth_bytes))
    except Exception as error:
        print(f"cannot generate output {output}: {error}", file=sys.stderr)
        return 1
    staging = None
    active_path = output.parent
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent)
        )
        active_path = staging / "telemetry.json"
        active_path.write_bytes(telemetry_bytes)
        active_path = staging / "ground-truth.json"
        active_path.write_bytes(truth_bytes)
        active_path = output
        staging.rename(output)
        staging = None
    except Exception as error:
        print(f"cannot prepare output at {active_path}: {error}", file=sys.stderr)
        if staging is not None:
            try:
                shutil.rmtree(staging)
            except OSError as cleanup_error:
                print(
                    f"cannot clean staging {staging}: {cleanup_error}", file=sys.stderr
                )
        return 1
    print(
        json.dumps(
            {
                "ground_truth": str(output / "ground-truth.json"),
                "ground_truth_sha256": hashlib.sha256(truth_bytes).hexdigest(),
                "telemetry": str(output / "telemetry.json"),
                "telemetry_sha256": hashlib.sha256(telemetry_bytes).hexdigest(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0
