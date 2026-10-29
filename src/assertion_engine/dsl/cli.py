"""The assertion-rules command: check and dump a rule set (contracts/cli.md).

Every command reads the file and loads the whole rule set first, so an invalid
rule set prints its one diagnostic and exits 1 before a command does anything
else. Bad arguments, an unreadable file and an unknown rule exit 2.
"""

import argparse
import sys
import tomllib
from pathlib import Path

from assertion_engine.artifacts import canonical_bytes
from assertion_engine.dsl.errors import Diagnostic, FileLocation, RuleSetError
from assertion_engine.dsl.ruleset import load_ruleset
from assertion_engine.dsl.syntax import to_document


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="assertion-rules")
    commands = parser.add_subparsers(dest="command", required=True)
    # No abbreviations: check would otherwise take --rule X as --ruleset X.
    check = commands.add_parser(
        "check", help="load and check a rule set", allow_abbrev=False
    )
    check.add_argument("--ruleset", required=True)
    dump = commands.add_parser(
        "dump", help="write a rule's canonical syntax tree", allow_abbrev=False
    )
    dump.add_argument("--ruleset", required=True)
    dump.add_argument("--rule", required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return error.code
    try:
        data = Path(args.ruleset).read_bytes()
    except OSError as error:
        print(f"{args.ruleset}: cannot read: {error.strerror}", file=sys.stderr)
        return 2
    try:
        ruleset = load_ruleset(data)
    except RuleSetError as error:
        print(_format(args.ruleset, data, error.diagnostic), file=sys.stderr)
        return 1
    if args.command == "check":
        rules, derived = len(ruleset.rules), len(ruleset.derived)
        parameters = len(ruleset.parameters)
        print(f"ok: {rules} rules, {derived} derived, {parameters} parameters")
        return 0
    if args.rule not in ruleset.rules:
        print(f"unknown rule: {args.rule}", file=sys.stderr)
        return 2
    tree = ruleset.rules[args.rule].annotations.tree
    sys.stdout.buffer.write(
        canonical_bytes({"rule": args.rule, "tree": to_document(tree)})
    )
    return 0


def _format(path: str, data: bytes, diagnostic: Diagnostic) -> str:
    """The diagnostic's header; an expression location adds a caret block."""
    location = diagnostic.location
    if isinstance(location, FileLocation):
        position = f"{location.file_line}:{location.file_column}"
        return f"{path}:{position}: {diagnostic.code}: {diagnostic.message}"
    if location.rule is not None:
        owner, section, name = f"rule {location.rule}", "rules", location.rule
    else:
        owner, section = f"derived {location.derived}", "derived"
        name = location.derived
    # Expression locations come only after loading steps 1-3 passed, so the
    # bytes decode again and hold this owner's expression.
    expression = tomllib.loads(data.decode("utf-8"))[section][name]["expression"]
    line = expression.split("\n")[location.line - 1]
    width = location.end_column - location.column
    caret = " " * (location.column - 1) + "^" * width
    position = f"{location.line}:{location.column}"
    header = f"{path}: {owner}: {position}: {diagnostic.code}: {diagnostic.message}"
    return f"{header}\n    {line}\n    {caret}"
