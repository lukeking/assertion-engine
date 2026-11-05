"""The assertion-rules command: check a rule set, dump a rule's syntax tree or
draw it as a PNG (contracts/cli.md).

Every command reads the file and loads the whole rule set first, so an invalid
rule set prints its one diagnostic and exits 1 before a command does anything
else. Bad arguments, an unreadable file, an unknown rule, an existing output
and an output that cannot be written (its directory missing, say) exit 2.
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
    tree = commands.add_parser(
        "tree", help="draw a rule's checked syntax tree as a PNG", allow_abbrev=False
    )
    tree.add_argument("--ruleset", required=True)
    tree.add_argument("--rule", required=True)
    tree.add_argument("--output", required=True)
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
    rule = ruleset.rules[args.rule]
    if args.command == "dump":
        document = {"rule": args.rule, "tree": to_document(rule.annotations.tree)}
        sys.stdout.buffer.write(canonical_bytes(document))
        return 0
    # Imported here: Matplotlib takes longer to import than check or dump run.
    from assertion_engine.dsl.tree_view import render

    try:
        render(rule.expression, rule.annotations, Path(args.output))
    except FileExistsError:
        print(f"output exists: {args.output}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"{args.output}: cannot write: {error.strerror}", file=sys.stderr)
        return 2
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
