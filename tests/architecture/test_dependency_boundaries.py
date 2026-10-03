"""FR-016: executable import boundaries and empty future M0 packages."""

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "assertion_engine"
RESERVED_PACKAGES = ("dsl", "evaluator", "fuzzer")
FORBIDDEN_DEPENDENCIES = {
    "fuzzer": ("assertion_engine.dsl", "assertion_engine.evaluator"),
    "playback": ("assertion_engine.simulator",),
}


def import_targets(node: ast.Import | ast.ImportFrom, package: str) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    base = resolve_name("." * node.level + (node.module or ""), package)
    return [
        base if alias.name == "*" else f"{base}.{alias.name}" for alias in node.names
    ]


def dependency_violations(package_root: Path) -> list[tuple[str, int, str]]:
    """Return source path, line and forbidden target for static Python imports."""
    violations = []
    for owner, forbidden in FORBIDDEN_DEPENDENCIES.items():
        for path in sorted((package_root / owner).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            package = ".".join(path.relative_to(package_root.parent).parts[:-1])
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                for target in import_targets(node, package):
                    if any(
                        target == prefix or target.startswith(prefix + ".")
                        for prefix in forbidden
                    ):
                        violations.append(
                            (
                                path.relative_to(package_root).as_posix(),
                                node.lineno,
                                target,
                            )
                        )
    return sorted(violations, key=lambda violation: (violation[0], violation[1]))


def reserved_behavior_violations(package_root: Path) -> list[tuple[str, int, str]]:
    """M0 reserved packages contain only comments, a module docstring or pass."""
    violations = []
    for package in RESERVED_PACKAGES:
        for path in sorted((package_root / package).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            body = tree.body[1:] if ast.get_docstring(tree) is not None else tree.body
            for node in body:
                if not isinstance(node, ast.Pass):
                    violations.append(
                        (
                            path.relative_to(package_root).as_posix(),
                            node.lineno,
                            type(node).__name__,
                        )
                    )
    return violations


def source_tree(tmp_path: Path, relative_path: str, source: str) -> Path:
    """Write source fixtures only beneath pytest's explicit temporary directory."""
    package_root = tmp_path / "src" / "assertion_engine"
    for name in (*RESERVED_PACKAGES, "playback", "simulator"):
        directory = package_root / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    path = package_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    parent = path.parent
    while parent != package_root:
        (parent / "__init__.py").touch()
        parent = parent.parent
    path.write_text(source, encoding="utf-8")
    return package_root


@pytest.mark.parametrize(
    ("relative_path", "source", "line", "target"),
    [
        ("fuzzer/inject.py", "import assertion_engine.dsl", 1, "assertion_engine.dsl"),
        (
            "fuzzer/inject.py",
            "import assertion_engine.dsl.ast as grammar",
            1,
            "assertion_engine.dsl.ast",
        ),
        (
            "fuzzer/inject.py",
            "from assertion_engine.dsl.grammar import parse as parse_rule",
            1,
            "assertion_engine.dsl.grammar.parse",
        ),
        (
            "fuzzer/inject.py",
            "import assertion_engine.evaluator.semantics as rules",
            1,
            "assertion_engine.evaluator.semantics",
        ),
        (
            "fuzzer/inject.py",
            "from assertion_engine import evaluator as rules",
            1,
            "assertion_engine.evaluator",
        ),
        (
            "fuzzer/inject.py",
            "from assertion_engine import dsl",
            1,
            "assertion_engine.dsl",
        ),
        (
            "fuzzer/inject.py",
            "from .. import dsl as grammar",
            1,
            "assertion_engine.dsl",
        ),
        (
            "fuzzer/inject.py",
            "from ..dsl import ast as rule_ast",
            1,
            "assertion_engine.dsl.ast",
        ),
        (
            "fuzzer/inject.py",
            "from ..evaluator import semantics",
            1,
            "assertion_engine.evaluator.semantics",
        ),
        (
            "fuzzer/__init__.py",
            "from .. import evaluator",
            1,
            "assertion_engine.evaluator",
        ),
        ("fuzzer/inject.py", "from ..dsl import *", 1, "assertion_engine.dsl"),
        (
            "fuzzer/nested/inject.py",
            "from ... import evaluator",
            1,
            "assertion_engine.evaluator",
        ),
        (
            "fuzzer/nested/__init__.py",
            "from ...dsl import grammar",
            1,
            "assertion_engine.dsl.grammar",
        ),
        (
            "fuzzer/inject.py",
            "def inject():\n    from .. import evaluator",
            2,
            "assertion_engine.evaluator",
        ),
        (
            "fuzzer/inject.py",
            "import json, assertion_engine.dsl.ast as grammar",
            1,
            "assertion_engine.dsl.ast",
        ),
        (
            "playback/view.py",
            "import assertion_engine.simulator",
            1,
            "assertion_engine.simulator",
        ),
        (
            "playback/view.py",
            "import assertion_engine.simulator.scenario as motion",
            1,
            "assertion_engine.simulator.scenario",
        ),
        (
            "playback/view.py",
            "from assertion_engine.simulator.scenario import generate as render",
            1,
            "assertion_engine.simulator.scenario.generate",
        ),
        (
            "playback/view.py",
            "from assertion_engine import simulator as motion",
            1,
            "assertion_engine.simulator",
        ),
        (
            "playback/view.py",
            "from .. import simulator",
            1,
            "assertion_engine.simulator",
        ),
        (
            "playback/view.py",
            "from ..simulator import scenario as motion",
            1,
            "assertion_engine.simulator.scenario",
        ),
        (
            "playback/__init__.py",
            "from ..simulator import *",
            1,
            "assertion_engine.simulator",
        ),
        (
            "playback/nested/__init__.py",
            "from ... import simulator",
            1,
            "assertion_engine.simulator",
        ),
        (
            "playback/nested/view.py",
            "if TYPE_CHECKING:\n    from ...simulator import config",
            2,
            "assertion_engine.simulator.config",
        ),
    ],
)
def test_FR016_scanner_rejects_forbidden_imports(
    tmp_path, relative_path, source, line, target
):
    package_root = source_tree(tmp_path, relative_path, source)
    assert dependency_violations(package_root) == [(relative_path, line, target)]


@pytest.mark.parametrize(
    ("relative_path", "source"),
    [
        ("fuzzer/inject.py", "import assertion_engine.telemetry as contract"),
        (
            "fuzzer/inject.py",
            "from assertion_engine.telemetry import TelemetrySnapshot",
        ),
        ("fuzzer/inject.py", "from .. import telemetry as contract"),
        ("fuzzer/inject.py", "from ..artifacts import canonical_bytes"),
        ("fuzzer/nested/__init__.py", "from ... import telemetry"),
        ("fuzzer/inject.py", "import evaluator as rules"),
        ("fuzzer/inject.py", "import other.assertion_engine.dsl.ast"),
        ("fuzzer/inject.py", "import assertion_engine.evaluator_helpers"),
        ("fuzzer/inject.py", "from assertion_engine import dsl_helpers"),
        ("fuzzer/inject.py", "from . import evaluator"),
        ("fuzzer/nested/inject.py", "from ..dsl import ast"),
        ("fuzzer/inject.py", "from math import sqrt as evaluator"),
        ("playback/view.py", "import assertion_engine.telemetry"),
        ("playback/view.py", "from ..artifacts import validate_artifact_pair"),
        ("playback/view.py", "from .. import telemetry"),
        ("playback/nested/view.py", "from ...telemetry import TelemetrySnapshot"),
        ("playback/view.py", "import simulator"),
        ("playback/view.py", "import other.assertion_engine.simulator"),
        ("playback/view.py", "from assertion_engine import simulator_helpers"),
        ("playback/view.py", "from . import simulator"),
        ("playback/nested/view.py", "from ..simulator import scenario"),
        ("playback/view.py", "from math import sqrt as simulator"),
        (
            "playback/view.py",
            '# import assertion_engine.simulator\n"from .. import simulator"',
        ),
        ("simulator/generate.py", "from assertion_engine import evaluator"),
    ],
)
def test_FR016_scanner_accepts_neutral_and_unrelated_imports(
    tmp_path, relative_path, source
):
    package_root = source_tree(tmp_path, relative_path, source)
    assert dependency_violations(package_root) == []


def test_FR016_scanner_reports_all_forbidden_targets_with_source_locations(tmp_path):
    package_root = source_tree(
        tmp_path,
        "fuzzer/inject.py",
        "from assertion_engine import telemetry, evaluator as rules, dsl as grammar\n"
        "from ..dsl import ast\n",
    )
    assert dependency_violations(package_root) == [
        ("fuzzer/inject.py", 1, "assertion_engine.evaluator"),
        ("fuzzer/inject.py", 1, "assertion_engine.dsl"),
        ("fuzzer/inject.py", 2, "assertion_engine.dsl.ast"),
    ]


@pytest.mark.parametrize("package", RESERVED_PACKAGES)
@pytest.mark.parametrize(
    ("source", "node_type"),
    [
        ("def run():\n    pass", "FunctionDef"),
        ("class Rule:\n    pass", "ClassDef"),
        ("enabled = True", "Assign"),
        ("run()", "Expr"),
        ("from .. import telemetry", "ImportFrom"),
    ],
)
def test_FR016_reserved_packages_reject_executable_m0_content(
    tmp_path, package, source, node_type
):
    relative_path = f"{package}/nested/implementation.py"
    package_root = source_tree(tmp_path, relative_path, source)
    assert reserved_behavior_violations(package_root) == [(relative_path, 1, node_type)]


@pytest.mark.parametrize("package", RESERVED_PACKAGES)
@pytest.mark.parametrize(
    "source", ["", "# Reserved for a later milestone.\n", '"""Reserved."""\npass\n']
)
def test_FR016_reserved_packages_accept_empty_placeholders(tmp_path, package, source):
    package_root = source_tree(tmp_path, f"{package}/__init__.py", source)
    assert reserved_behavior_violations(package_root) == []


def test_FR016_production_dependency_boundaries():
    for package in ("fuzzer", "playback"):
        assert (PACKAGE_ROOT / package / "__init__.py").is_file()
    assert dependency_violations(PACKAGE_ROOT) == []


def test_FR016_production_future_packages_are_empty():
    for package in RESERVED_PACKAGES:
        assert (PACKAGE_ROOT / package / "__init__.py").is_file()
    assert reserved_behavior_violations(PACKAGE_ROOT) == []
