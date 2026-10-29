"""Closed diagnostic codes, diagnostic locations and the rule-set failure.

Codes follow data-model.md "Diagnostic codes (closed list)" in stage order.
Loading is fail-closed with first error wins, so a failure carries one diagnostic.
"""

from dataclasses import dataclass

CODES = (
    # lexer
    "invalid_character",
    "invalid_number",
    # parser
    "empty_expression",
    "unexpected_token",
    "unexpected_end",
    "unclosed_parenthesis",
    "trailing_input",
    "chained_comparison",
    "reserved_word",
    "invalid_axis",
    "nesting_too_deep",
    # rule set
    "invalid_ruleset",
    "unknown_unit",
    "name_conflict",
    # checker
    "unknown_name",
    "arity_mismatch",
    "type_mismatch",
    "dimension_mismatch",
    "not_boolean_rule",
    "nonpositive_duration",
    "derived_unit_mismatch",
    "derived_cycle",
)


@dataclass(frozen=True)
class ExpressionLocation:
    """Positions within one expression string.

    The lexer and parser see only the text and leave both owners unset; the
    rule-set loader names the rule or derived quantity it was parsing.
    """

    line: int
    column: int
    end_column: int
    fragment: str
    rule: str | None = None
    derived: str | None = None

    def __post_init__(self):
        if self.rule is not None and self.derived is not None:
            raise ValueError("expression location names at most one rule or derived")


@dataclass(frozen=True)
class FileLocation:
    """Position within the rule-set file, for TOML syntax errors."""

    file_line: int
    file_column: int


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    location: ExpressionLocation | FileLocation

    def __post_init__(self):
        if self.code not in CODES:
            raise ValueError(f"{self.code}: not a diagnostic code")


class RuleSetError(ValueError):
    """A rule set was rejected at its first diagnostic."""

    def __init__(self, diagnostic: Diagnostic):
        if not isinstance(diagnostic, Diagnostic):
            raise TypeError("RuleSetError carries one Diagnostic")
        super().__init__(diagnostic)
        self.diagnostic = diagnostic
