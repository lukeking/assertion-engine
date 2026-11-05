"""Fail-closed rule-set loading (data-model.md "Loading pipeline").

load_ruleset takes a rule-set file's bytes (reading the file is the caller's
job, plan.md "Structure Decision") and runs the nine steps in order: the
first error raises RuleSetError and nothing partial is returned. Inside a
step, entries go in file order; step 3 checks every name, parameters before
derived quantities, before any unit.

tomllib keeps no positions (research.md Decision 7). A TOML syntax error has
tomllib's own line and column; any other error of steps 1-3 points at the
start of the line that defines the offending key, or the table that lacks
one, and a missing top-level key at the start of the file. Expression errors
of steps 4-8 name the derived quantity or rule they belong to.
"""

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

from assertion_engine.dsl.checker import Annotations, Scope, check_derived, check_rule
from assertion_engine.dsl.errors import Diagnostic, FileLocation, RuleSetError
from assertion_engine.dsl.lexer import KEYWORDS, RESERVED_WORDS
from assertion_engine.dsl.parser import parse
from assertion_engine.dsl.syntax import Node
from assertion_engine.dsl.units import UNITS
from assertion_engine.dsl.vocabulary import BUILT_IN_DERIVED, FIELDS, FUNCTIONS

SCHEMA_VERSION = "1.0.0"
CATEGORIES = ("threshold", "logic", "temporal", "trend")
_NAME = re.compile(r"[a-z][a-z0-9_]*")
# contracts/ruleset.md "File shape": section -> (entry name, the entry's keys).
_SECTIONS = {
    "parameters": (_NAME, ("unit",)),
    "derived": (_NAME, ("unit", "expression")),
    "rules": (re.compile(r"[a-z0-9]+(-[a-z0-9]+)*"), ("category", "expression")),
}
_DECLARATIONS = ("parameters", "derived")

type KeyPath = tuple[str, ...]  # TOML keys from the document root


@dataclass(frozen=True, eq=False)
class Derived:
    unit: str
    expression: str
    annotations: Annotations  # the checked tree is annotations.tree


@dataclass(frozen=True, eq=False)
class Rule:
    category: str
    expression: str
    annotations: Annotations


@dataclass(frozen=True, eq=False)
class RuleSet:
    """A checked rule set (data-model.md "Rule set"); mappings keep file order.

    parameters maps name -> unit and derived holds the rule set's own
    quantities; scope.derived has the built-in ones first, then those.
    """

    schema_version: str
    parameters: Mapping[str, str]
    derived: Mapping[str, Derived]
    rules: Mapping[str, Rule]
    scope: Scope


def load_ruleset(data: bytes) -> RuleSet:
    """Load and check one rule-set file's bytes; raise at the first error."""
    text = _decode(data)  # 1
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        location = FileLocation(error.lineno, error.colno)
        raise RuleSetError(Diagnostic("invalid_ruleset", error.msg, location)) from None
    except RecursionError:  # tomllib recurses once per nested array or table
        message = "TOML nesting is too deep to decode"
        location = FileLocation(1, 1)
        raise RuleSetError(Diagnostic("invalid_ruleset", message, location)) from None
    _check_shape(document, text)  # 2
    _check_names(document, text)  # 3
    _check_units(document, text)
    built_in = {  # 4: a failure here is a vocabulary bug
        name: (unit, definition, _parse(definition, derived=name))
        for name, (unit, definition) in BUILT_IN_DERIVED.items()
    }
    derived_tables = document.get("derived", {})
    derived = {  # 5
        name: (
            table["unit"],
            table["expression"],
            _parse(table["expression"], derived=name),
        )
        for name, table in derived_tables.items()
    }
    parameters = {
        name: table["unit"] for name, table in document.get("parameters", {}).items()
    }
    scope = check_derived(built_in, derived, parameters)  # 6
    rule_tables = document["rules"]
    trees = {  # 7
        short_name: _parse(table["expression"], rule=short_name)
        for short_name, table in rule_tables.items()
    }
    rules = {}
    for short_name, table in rule_tables.items():  # 8
        text = table["expression"]
        annotations = check_rule(short_name, text, trees[short_name], scope)
        rules[short_name] = Rule(table["category"], text, annotations)
    own_derived = {
        name: Derived(table["unit"], table["expression"], scope.derived[name])
        for name, table in derived_tables.items()
    }
    return RuleSet(  # 9
        document["schema_version"],
        MappingProxyType(parameters),
        MappingProxyType(own_derived),
        MappingProxyType(rules),
        scope,
    )


def _decode(data: bytes) -> str:
    """UTF-8 text, or invalid_ruleset at the first byte that does not decode."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        before = data[: error.start]
        line_start = before.rfind(b"\n") + 1
        column = len(before[line_start:].decode("utf-8")) + 1
        location = FileLocation(before.count(b"\n") + 1, column)
        message = f"not UTF-8: byte {data[error.start]:#04x}"
        raise RuleSetError(Diagnostic("invalid_ruleset", message, location)) from None


def _check_shape(document: dict, text: str):
    """Keys, value types, names and categories; then what is missing."""
    for key, value in document.items():
        if key == "schema_version":
            if value != SCHEMA_VERSION:
                message = f"schema_version must be {SCHEMA_VERSION!r}, not {value!r}"
                raise _file_error("invalid_ruleset", message, text, (key,))
        elif key in _SECTIONS:
            _check_section(key, value, text)
        else:
            message = f"{key!r} is not a rule-set key"
            raise _file_error("invalid_ruleset", message, text, (key,))
    if "schema_version" not in document:
        raise _file_error("invalid_ruleset", "schema_version is missing", text, ())
    if not document.get("rules"):
        path = ("rules",) if "rules" in document else ()
        message = "at least one rule is required"
        raise _file_error("invalid_ruleset", message, text, path)


def _check_section(section: str, entries, text: str):
    if not isinstance(entries, dict):
        message = f"{section} must be a table"
        raise _file_error("invalid_ruleset", message, text, (section,))
    pattern, keys = _SECTIONS[section]
    for name, entry in entries.items():
        path, label = (section, name), f"{section}.{name}"
        if not pattern.fullmatch(name):
            message = f"{name!r} does not match the {section} name pattern"
            raise _file_error("invalid_ruleset", message, text, path)
        if not isinstance(entry, dict):
            message = f"{label} must be a table"
            raise _file_error("invalid_ruleset", message, text, path)
        for key, value in entry.items():
            if key not in keys:
                message = f"{key!r} is not a key of {label} ({', '.join(keys)})"
                raise _file_error("invalid_ruleset", message, text, (*path, key))
            if not isinstance(value, str):
                message = f"{label}.{key} must be a string"
                raise _file_error("invalid_ruleset", message, text, (*path, key))
            if key == "category" and value not in CATEGORIES:
                message = f"{value!r} is not a category ({', '.join(CATEGORIES)})"
                raise _file_error("invalid_ruleset", message, text, (*path, key))
        for key in keys:
            if key not in entry:
                message = f"{label} is missing {key!r}"
                raise _file_error("invalid_ruleset", message, text, path)


def _check_names(document: dict, text: str):
    """Declared names are not reserved, not the language's or vocabulary's,
    and not declared twice (TOML itself rejects twice in one section)."""
    taken = (
        (KEYWORDS, "keyword"),
        (FIELDS, "field"),
        (FUNCTIONS, "function"),
        (BUILT_IN_DERIVED, "built-in derived quantity"),
    )
    declared = set()
    for section in _DECLARATIONS:
        for name in document.get(section, {}):
            path = (section, name)
            if name in RESERVED_WORDS:
                message = f"{name!r} is a reserved word"
                raise _file_error("reserved_word", message, text, path)
            for words, kind in taken:
                if name in words:
                    message = f"{name!r} is already a {kind}"
                    raise _file_error("name_conflict", message, text, path)
            if name in declared:
                message = f"{name!r} is already declared as a parameter"
                raise _file_error("name_conflict", message, text, path)
            declared.add(name)


def _check_units(document: dict, text: str):
    for section in _DECLARATIONS:
        for name, entry in document.get(section, {}).items():
            if entry["unit"] not in UNITS:
                message = f"{entry['unit']!r} is not a unit ({', '.join(UNITS)})"
                path = (section, name, "unit")
                raise _file_error("unknown_unit", message, text, path)


def _parse(text: str, **owner) -> Node:
    """Parse one expression; a syntax error names owner (rule= or derived=)."""
    try:
        return parse(text)
    except RuleSetError as error:
        diagnostic = error.diagnostic
        location = replace(diagnostic.location, **owner)
        raise RuleSetError(replace(diagnostic, location=location)) from None


def _file_error(code: str, message: str, text: str, path: KeyPath) -> RuleSetError:
    return RuleSetError(Diagnostic(code, message, _locate(text, path)))


def _locate(text: str, path: KeyPath) -> FileLocation:
    """The first non-blank column of the line that defines path's key.

    TOML writes a key, its "=" and the start of its value on one line, and a
    valid document's line prefixes parse unless they cut a multi-line value.
    So the first parsing prefix that defines path ends on the key's line, or,
    after prefixes that did not parse, on its value's last line, and the key
    is on the first of those. The empty path is the start of the file.
    """
    if not path:
        return FileLocation(1, 1)
    lines = text.split("\n")
    unparsed_from = None
    for count in range(1, len(lines) + 1):
        try:
            prefix = tomllib.loads("\n".join(lines[:count]))
        except tomllib.TOMLDecodeError:
            unparsed_from = unparsed_from or count
            continue
        if _defines(prefix, path):
            line = unparsed_from or count
            content = lines[line - 1]
            return FileLocation(line, len(content) - len(content.lstrip(" \t")) + 1)
        unparsed_from = None
    raise ValueError(f"the document has no key {'.'.join(path)}")


def _defines(document: dict, path: KeyPath) -> bool:
    node = document
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return True
