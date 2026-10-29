"""The rule DSL's public API (plan.md "Source Code").

load_ruleset runs the fail-closed loading pipeline over a rule-set file's
bytes; parse_expression parses one expression on its own. Both raise
RuleSetError carrying one Diagnostic.
"""

from assertion_engine.dsl.errors import Diagnostic, RuleSetError
from assertion_engine.dsl.parser import parse
from assertion_engine.dsl.ruleset import load_ruleset
from assertion_engine.dsl.syntax import Node

__all__ = ["Diagnostic", "RuleSetError", "load_ruleset", "parse_expression"]


def parse_expression(text: str) -> Node:
    """Parse one expression; a syntax error's location names no owner.

    A thin wrapper over parser.parse without its binding_powers and collector
    arguments, which exist for the SC-006 and SC-007 tests.
    """
    return parse(text)
