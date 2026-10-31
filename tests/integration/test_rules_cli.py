"""FR-011, contracts/cli.md: the registered assertion-rules command.

Rule sets are written line by line into tmp_path, so expected file locations
can be counted by hand and expected expression locations counted in the
expression string. BASIC copies the 7 threshold and logic rules of
rules/corpus.toml (Gate 「基本規則」) and the declarations they need; the corpus
file itself is only read, in place, by the check of the whole corpus.
"""

import errno
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "rules" / "corpus.toml"
GOLDEN_DIR = REPO_ROOT / "tests" / "fixtures" / "rule_trees"
EXECUTABLE = Path(sys.executable).parent / "assertion-rules"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

BASIC = (
    'schema_version = "1.0.0"',
    "",
    "[parameters.cruise_speed_mps]",
    'unit = "m/s"',
    "",
    "[parameters.descent_rate_mps]",
    'unit = "m/s"',
    "",
    "[parameters.battery_floor_percent]",
    'unit = "%"',
    "",
    "[parameters.altitude_ceiling_m]",
    'unit = "m"',
    "",
    "[parameters.horizontal_speed_max_mps]",
    'unit = "m/s"',
    "",
    "[parameters.drain_rate_percent_per_s]",
    'unit = "%/s"',
    "",
    "[parameters.return_reserve_percent]",
    'unit = "%"',
    "",
    "[parameters.fence_radius_m]",
    'unit = "m"',
    "",
    "[parameters.fence_altitude_m]",
    'unit = "m"',
    "",
    "[parameters.battery_low_percent]",
    'unit = "%"',
    "",
    "[parameters.low_battery_radius_m]",
    'unit = "m"',
    "",
    "[parameters.near_ground_altitude_m]",
    'unit = "m"',
    "",
    "[parameters.near_ground_descent_max_mps]",
    'unit = "m/s"',
    "",
    "[parameters.descent_max_mps]",
    'unit = "m/s"',
    "",
    "[derived.return_time_s]",
    'unit = "s"',
    'expression = "home_distance_m / cruise_speed_mps + altitude_m / descent_rate_mps"',
    "",
    "[rules.battery-floor]",
    'category = "threshold"',
    'expression = "battery_percent >= battery_floor_percent"',
    "",
    "[rules.altitude-ceiling]",
    'category = "threshold"',
    'expression = "altitude_m <= altitude_ceiling_m"',
    "",
    "[rules.horizontal-speed-limit]",
    'category = "threshold"',
    'expression = "horizontal_speed_mps <= horizontal_speed_max_mps"',
    "",
    "[rules.return-reserve]",
    'category = "threshold"',
    'expression = "battery_percent > return_time_s * drain_rate_percent_per_s'
    ' + return_reserve_percent"',
    "",
    "[rules.geofence-cylinder]",
    'category = "logic"',
    'expression = "home_distance_m <= fence_radius_m'
    ' and altitude_m <= fence_altitude_m"',
    "",
    "[rules.low-battery-stay-close]",
    'category = "logic"',
    'expression = "battery_percent < battery_low_percent'
    ' implies home_distance_m <= low_battery_radius_m"',
    "",
    "[rules.descent-speed-near-ground]",
    'category = "logic"',
    'expression = """',
    "descent_speed_mps <= (if altitude_m < near_ground_altitude_m",
    "                      then near_ground_descent_max_mps",
    '                      else descent_max_mps)"""',
)
# No [derived] table: the 4 built-in derived quantities are never counted.
NO_DERIVED = (
    'schema_version = "1.0.0"',
    "",
    "[parameters.battery_floor_percent]",
    'unit = "%"',
    "",
    "[rules.battery-floor]",
    'category = "threshold"',
    'expression = "battery_percent >= battery_floor_percent"',
)

# Invalid rule sets: (lines, --ruleset as given, the whole expected stderr).
RULE_ON_LINE_2 = (
    (
        'schema_version = "1.0.0"',
        "",
        "[parameters.battery_floor_percent]",
        'unit = "%"',
        "",
        "[rules.battery-typo]",
        'category = "threshold"',
        'expression = """',
        "battery_percent >=",
        '  battery_flor_percent"""',
    ),
    "bad.toml",
    "bad.toml: rule battery-typo: 2:3: unknown_name: "
    "'battery_flor_percent' is not a field, derived quantity or parameter\n"
    "      battery_flor_percent\n"
    "      ^^^^^^^^^^^^^^^^^^^^\n",
)
DERIVED = (
    (
        'schema_version = "1.0.0"',
        "",
        "[parameters.descent_rate_mps]",
        'unit = "m/s"',
        "",
        "[derived.descent_time_s]",
        'unit = "s"',
        'expression = "altitude_m / (descent_rate_mps"',
        "",
        "[rules.battery-floor]",
        'category = "threshold"',
        'expression = "battery_percent >= 0"',
    ),
    "./bad.toml",
    "./bad.toml: derived descent_time_s: 1:14: unclosed_parenthesis: "
    "'(' is never closed\n"
    "    altitude_m / (descent_rate_mps\n"
    "                 ^\n",
)
# The end of input is the one column past the text, with an empty fragment.
AT_END = (
    (
        'schema_version = "1.0.0"',
        "",
        "[rules.battery-floor]",
        'category = "threshold"',
        'expression = "battery_percent >="',
    ),
    "bad.toml",
    "bad.toml: rule battery-floor: 1:19: unexpected_end: expression ends too early\n"
    "    battery_percent >=\n"
    "                      ^\n",
)
TOML_SYNTAX = (
    (
        'schema_version = "1.0.0"',
        "",
        "[rules.battery-floor]",
        'category = "threshold"',
        'expression = "battery_percent >= 0',
    ),
    "bad.toml",
    "bad.toml:5:35: invalid_ruleset: Illegal character '\\n'\n",
)
# A file location from loading step 3, at the key's first non-blank column.
UNKNOWN_UNIT = (
    (
        'schema_version = "1.0.0"',
        "",
        "[parameters.battery_floor_percent]",
        '  unit = "percent"',
        "",
        "[rules.battery-floor]",
        'category = "threshold"',
        'expression = "battery_percent >= battery_floor_percent"',
    ),
    "bad.toml",
    "bad.toml:4:3: unknown_unit: 'percent' is not a unit (1, %, m, s, m/s, %/s)\n",
)


def write(tmp_path: Path, name: str, lines: tuple[str, ...]) -> Path:
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run(tmp_path: Path, *arguments: str, text: bool = True):
    assert EXECUTABLE.is_file(), "test must exercise the registered console script"
    return subprocess.run(
        [str(EXECUTABLE), *arguments],
        cwd=tmp_path,
        capture_output=True,
        text=text,
        check=False,
    )


def test_check_accepts_the_basic_rule_set(tmp_path):
    write(tmp_path, "basic.toml", BASIC)
    result = run(tmp_path, "check", "--ruleset", "basic.toml")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "ok: 7 rules, 1 derived, 14 parameters\n"
    assert result.stderr == ""


def test_check_accepts_the_whole_corpus(tmp_path):
    # SC-004: all 17 corpus rules load, temporal and trend rules included.
    result = run(tmp_path, "check", "--ruleset", str(CORPUS))
    assert result.returncode == 0, result.stderr
    assert result.stdout == "ok: 17 rules, 1 derived, 27 parameters\n"
    assert result.stderr == ""


def test_check_counts_only_the_rule_sets_own_derived(tmp_path):
    write(tmp_path, "small.toml", NO_DERIVED)
    result = run(tmp_path, "check", "--ruleset", "small.toml")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "ok: 1 rules, 0 derived, 1 parameters\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "command",
    [
        ("check",),
        ("dump", "--rule", "no-such-rule"),
        ("tree", "--rule", "no-such-rule", "--output", "out.png"),
    ],
    ids=["check", "dump", "tree"],
)
@pytest.mark.parametrize(
    ("lines", "given", "expected"),
    [RULE_ON_LINE_2, DERIVED, AT_END, TOML_SYNTAX, UNKNOWN_UNIT],
    ids=["rule-on-line-2", "derived", "at-end", "toml-syntax", "unknown-unit"],
)
def test_invalid_rule_set_prints_one_diagnostic(
    tmp_path, command, lines, given, expected
):
    # dump and tree name an unknown rule: loading the whole rule set comes first.
    write(tmp_path, "bad.toml", lines)
    result = run(tmp_path, command[0], "--ruleset", given, *command[1:])
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == expected
    assert [path.name for path in tmp_path.iterdir()] == ["bad.toml"]


def test_dump_writes_the_golden_bytes(tmp_path):
    write(tmp_path, "basic.toml", BASIC)
    result = run(
        tmp_path,
        "dump",
        "--ruleset",
        "basic.toml",
        "--rule",
        "battery-floor",
        text=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == (GOLDEN_DIR / "battery-floor.json").read_bytes()
    assert result.stderr == b""


def test_dump_rejects_an_unknown_rule(tmp_path):
    write(tmp_path, "basic.toml", BASIC)
    result = run(tmp_path, "dump", "--ruleset", "basic.toml", "--rule", "no-such-rule")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "unknown rule: no-such-rule\n"


def tree(tmp_path: Path, rule: str, output: str):
    return run(
        tmp_path,
        "tree",
        "--ruleset",
        "basic.toml",
        "--rule",
        rule,
        "--output",
        output,
    )


def test_tree_writes_a_png(tmp_path):
    write(tmp_path, "basic.toml", BASIC)
    result = tree(tmp_path, "descent-speed-near-ground", "descent.png")
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
    assert (tmp_path / "descent.png").read_bytes().startswith(PNG_SIGNATURE)
    # The staging file was linked into place and removed, not left beside it.
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "basic.toml",
        "descent.png",
    ]


# Exit 2 is also argparse's code for an unknown command: each case below checks
# its own stderr line and the files left, so a missing tree command fails it.
def test_tree_never_overwrites_an_existing_output(tmp_path):
    write(tmp_path, "basic.toml", BASIC)
    (tmp_path / "battery-floor.png").write_bytes(b"not mine")
    result = tree(tmp_path, "battery-floor", "battery-floor.png")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "output exists: battery-floor.png\n"
    assert (tmp_path / "battery-floor.png").read_bytes() == b"not mine"
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "basic.toml",
        "battery-floor.png",
    ]


def test_tree_rejects_an_unknown_rule(tmp_path):
    write(tmp_path, "basic.toml", BASIC)
    result = tree(tmp_path, "no-such-rule", "out.png")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "unknown rule: no-such-rule\n"
    assert [path.name for path in tmp_path.iterdir()] == ["basic.toml"]


def test_tree_output_directory_must_exist(tmp_path):
    write(tmp_path, "basic.toml", BASIC)
    result = tree(tmp_path, "battery-floor", "missing/battery-floor.png")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        f"missing/battery-floor.png: cannot write: {os.strerror(errno.ENOENT)}\n"
    )
    assert [path.name for path in tmp_path.iterdir()] == ["basic.toml"]


# Options are spelled out: an abbreviation such as --rule for --ruleset is unknown.
@pytest.mark.parametrize(
    "arguments",
    [
        (),
        ("check",),
        ("check", "--ruleset", "basic.toml", "--rule", "battery-floor"),
        ("dump", "--ruleset", "basic.toml"),
        ("dump", "--rule", "battery-floor"),
        ("dump", "--rules", "basic.toml", "--rule", "battery-floor"),
        ("tree", "--ruleset", "basic.toml", "--rule", "battery-floor"),
        (
            "tree",
            "--ruleset",
            "basic.toml",
            "--rule",
            "battery-floor",
            "--out",
            "out.png",
        ),
    ],
    ids=[
        "no-command",
        "check-without-ruleset",
        "check-with-rule",
        "dump-without-rule",
        "dump-without-ruleset",
        "dump-abbreviated-ruleset",
        "tree-without-output",
        "tree-abbreviated-output",
    ],
)
def test_bad_arguments_are_a_usage_error(tmp_path, arguments):
    write(tmp_path, "basic.toml", BASIC)
    result = run(tmp_path, *arguments)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("usage: assertion-rules")


@pytest.mark.parametrize(
    ("given", "command", "code"),
    [
        ("missing.toml", ("check",), errno.ENOENT),
        (".", ("dump", "--rule", "battery-floor"), errno.EISDIR),
    ],
    ids=["missing", "directory"],
)
def test_unreadable_rule_set_is_a_usage_error(tmp_path, given, command, code):
    result = run(tmp_path, command[0], "--ruleset", given, *command[1:])
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{given}: cannot read: {os.strerror(code)}\n"
