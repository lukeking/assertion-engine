"""Name resolution, arity, types and dimensions of parsed expressions.

Applies contracts/ruleset.md "Type and dimension rules" to syntax trees and
returns contracts/syntax-tree.md "Checker annotations": each node's type and
each Name node's resolution, keyed by node identity.

check_derived checks the 4 built-in derived quantities (parsed by the caller
from vocabulary.BUILT_IN_DERIVED, loading pipeline step 4) and then the rule
set's, in declaration order (data-model.md "Loading pipeline" step 6);
check_rule checks one rule against the resulting Scope (step 8). The first
error raises RuleSetError; nothing partial is returned.

Order inside one tree: depth first, children left to right, and a node's own
rule after all its children; a call resolves its function name, then infers
its arguments (their own errors first), then checks arity, then the argument
kinds. A derived quantity met by name
is checked on the spot, so its errors come before its dependent's; a name
whose quantity is still being checked closes a cycle (derived_cycle there).

A type_mismatch points at the first operand, in source order, whose kind the
construct rejects on its own; operands that are acceptable one by one but not
together (different kinds, vector * vector) point at the construct, as do
dimension mismatches.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from assertion_engine.dsl.errors import Diagnostic, ExpressionLocation, RuleSetError
from assertion_engine.dsl.syntax import (
    And,
    Arithmetic,
    Call,
    Compare,
    Component,
    Conditional,
    Implies,
    Name,
    Negate,
    Node,
    Number,
    Span,
)
from assertion_engine.dsl.units import Dimension, dimension_of
from assertion_engine.dsl.vocabulary import FIELDS, FUNCTIONS


@dataclass(frozen=True)
class Type:
    """bool, or a scalar or vector of one dimension."""

    kind: str
    dimension: Dimension | None = None

    def __str__(self) -> str:
        if self.dimension is None:
            return self.kind
        return f"{self.kind}[{self.dimension}]"


BOOL = Type("bool")
_DIMENSIONLESS = Type("scalar", Dimension())
_VALUES = ("scalar", "vector")
_FIELDS = MappingProxyType(
    {
        name: ("field", Type(kind, dimension_of(unit)))
        for name, (kind, unit) in FIELDS.items()
    }
)

type Resolution = tuple[str, Type]  # field, derived or parameter, and its type


@dataclass(frozen=True, eq=False)
class Annotations:
    """One checked tree's node types and Name resolutions.

    Keyed by node identity: nodes compare by value, so an equal node of
    another tree has no annotation here. The tree is kept so its node
    identities stay valid.
    """

    tree: Node
    types: Mapping[int, Type]
    resolutions: Mapping[int, str]

    def type_of(self, node: Node) -> Type:
        return self.types[id(node)]

    def resolution_of(self, node: Name) -> str:
        return self.resolutions[id(node)]


@dataclass(frozen=True, eq=False)
class Scope:
    """Every name a rule may use, once the derived quantities are checked."""

    names: Mapping[str, Resolution]
    derived: Mapping[str, Annotations]  # built-ins first, then declaration order


def check_derived(
    built_in: Mapping[str, tuple[str, str, Node]],
    derived: Mapping[str, tuple[str, str, Node]],
    parameters: Mapping[str, str],
) -> Scope:
    """Check the built-in and then the rule set's derived quantities.

    built_in and derived map name -> (unit, expression text, tree): the
    vocabulary's definitions and the rule set's, in file order. parameters
    maps name -> unit. The loader has already rejected name conflicts and
    undeclarable units. A parameter is a scalar of its unit.
    """
    declarations = {**built_in, **derived}
    values = dict(_FIELDS)
    for name, unit in parameters.items():
        values[name] = ("parameter", Type("scalar", dimension_of(unit)))
    graph = _DerivedGraph(declarations, values)
    names = {
        **values,
        **{name: ("derived", graph.check(name)) for name in declarations},
    }
    checked = {name: graph.checked[name] for name in declarations}
    return Scope(MappingProxyType(names), MappingProxyType(checked))


def check_rule(short_name: str, text: str, tree: Node, scope: Scope) -> Annotations:
    """Check one rule's tree, parsed from text; its root must be bool."""
    checker = _TreeChecker(
        text, {"rule": short_name}, lambda node: scope.names.get(node.name)
    )
    annotations = checker.check(tree)
    root = annotations.type_of(tree)
    if root != BOOL:
        raise checker.error(
            "not_boolean_rule", tree, f"a rule must be bool, not {root}"
        )
    return annotations


class _DerivedGraph:
    """Checks derived quantities depth first along their references."""

    def __init__(
        self,
        declarations: Mapping[str, tuple[str, str, Node]],
        values: Mapping[str, Resolution],
    ):
        self.declarations = declarations
        self.values = values  # fields and parameters
        self.checked: dict[str, Annotations] = {}
        self.path: list[str] = []  # quantities being checked, outermost first

    def check(self, name: str) -> Type:
        if name not in self.checked:
            unit, text, tree = self.declarations[name]
            self.path.append(name)
            checker = _TreeChecker(text, {"derived": name}, self.resolve)
            annotations = checker.check(tree)
            self.path.pop()
            inferred = annotations.type_of(tree)
            # bool has no dimension, so it never matches a declared unit.
            if inferred.dimension != dimension_of(unit):
                message = f"{name} is declared in {unit}, its expression is {inferred}"
                raise checker.error("derived_unit_mismatch", tree, message)
            self.checked[name] = annotations
        return self.checked[name].type_of(self.checked[name].tree)

    def resolve(self, node: Name) -> Resolution | None:
        if node.name not in self.declarations:
            return self.values.get(node.name)
        if node.name in self.path:
            owner = self.path[-1]
            cycle = [*self.path[self.path.index(node.name) :], node.name]
            message = f"derived quantities form a cycle: {' -> '.join(cycle)}"
            text = self.declarations[owner][1]
            raise _error("derived_cycle", message, node, text, derived=owner)
        return "derived", self.check(node.name)


class _TreeChecker:
    """Types one tree; diagnostics name its owner and point into its text."""

    def __init__(
        self, text: str, owner: dict, resolve: Callable[[Name], Resolution | None]
    ):
        self.text = text
        self.owner = owner
        self.resolve = resolve
        self.types: dict[int, Type] = {}
        self.resolutions: dict[int, str] = {}

    def check(self, tree: Node) -> Annotations:
        self.infer(tree)
        return Annotations(
            tree, MappingProxyType(self.types), MappingProxyType(self.resolutions)
        )

    def error(self, code: str, node: Node, message: str) -> RuleSetError:
        return _error(code, message, node, self.text, **self.owner)

    def infer(self, node: Node) -> Type:
        type_ = self._infer(node)
        self.types[id(node)] = type_
        return type_

    def _infer(self, node: Node) -> Type:
        match node:
            case Number():
                return _DIMENSIONLESS
            case Name():
                return self.name(node)
            case Negate(operand=operand):
                return self.require(operand, self.infer(operand), _VALUES, "unary '-'")
            case Component(target=target, axis=axis):
                vector = self.infer(target)
                self.require(target, vector, ("vector",), f"'.{axis}'")
                return Type("scalar", vector.dimension)
            case Arithmetic():
                return self.arithmetic(node)
            case Compare(op=op, left=left, right=right):
                left_type, right_type = self.infer(left), self.infer(right)
                self.require(left, left_type, ("scalar",), f"'{op}'")
                self.require(right, right_type, ("scalar",), f"'{op}'")
                left_type, right_type = self.zero(node, left_type, right_type)
                self.same(node, left_type, right_type, f"'{op}' operands")
                return BOOL
            case And(left=left, right=right):
                return self.logic(left, right, "'and'")
            case Implies(antecedent=antecedent, consequent=consequent):
                return self.logic(antecedent, consequent, "'implies'")
            case Conditional(condition=condition, then=then, else_=else_):
                condition_type = self.infer(condition)
                then_type, else_type = self.infer(then), self.infer(else_)
                self.require(condition, condition_type, ("bool",), "'if'")
                return self.same(node, then_type, else_type, "'if' branches")
            case Call():
                return self.call(node)
        raise NotImplementedError(f"{type(node).__name__} nodes are not checked yet")

    def name(self, node: Name) -> Type:
        resolution = self.resolve(node)
        if resolution is None:
            message = f"{node.name!r} is not a field, derived quantity or parameter"
            raise self.error("unknown_name", node, message)
        self.resolutions[id(node)], type_ = resolution
        return type_

    def arithmetic(self, node: Arithmetic) -> Type:
        left, right = self.infer(node.left), self.infer(node.right)
        construct = f"'{node.op}'"
        self.require(node.left, left, _VALUES, construct)
        if node.op == "/":
            self.require(node.right, right, ("scalar",), construct)
            return Type(left.kind, left.dimension / right.dimension)
        self.require(node.right, right, _VALUES, construct)
        if node.op == "*":
            if left.kind == right.kind == "vector":
                message = f"{construct} cannot multiply two vectors"
                raise self.error("type_mismatch", node, message)
            kind = "vector" if "vector" in (left.kind, right.kind) else "scalar"
            return Type(kind, left.dimension * right.dimension)
        left, right = self.zero(node, left, right)
        return self.same(node, left, right, f"{construct} operands")

    def call(self, node: Call) -> Type:
        if node.function not in FUNCTIONS:
            message = f"{node.function!r} is not a function ({', '.join(FUNCTIONS)})"
            raise self.error("unknown_name", node, message)
        arguments = [self.infer(argument) for argument in node.arguments]
        kinds, result = FUNCTIONS[node.function]
        if len(arguments) != len(kinds):
            count = len(arguments)
            message = f"{node.function}() takes {len(kinds)} argument(s), not {count}"
            raise self.error("arity_mismatch", node, message)
        for argument, type_, kind in zip(node.arguments, arguments, kinds):
            self.require(argument, type_, (kind,), f"{node.function}()")
        return Type(result, arguments[0].dimension)

    def logic(self, left: Node, right: Node, construct: str) -> Type:
        left_type, right_type = self.infer(left), self.infer(right)
        self.require(left, left_type, ("bool",), construct)
        self.require(right, right_type, ("bool",), construct)
        return BOOL

    def zero(self, node: Arithmetic | Compare, left: Type, right: Type):
        """Literal 0 takes the other operand's dimension (+, - and comparisons)."""
        if _is_zero(node.left):
            left = self.types[id(node.left)] = Type("scalar", right.dimension)
        elif _is_zero(node.right):
            right = self.types[id(node.right)] = Type("scalar", left.dimension)
        return left, right

    def require(self, node: Node, type_: Type, kinds: tuple, construct: str) -> Type:
        if type_.kind not in kinds:
            message = f"{construct} expects {' or '.join(kinds)}, not {type_}"
            raise self.error("type_mismatch", node, message)
        return type_

    def same(self, node: Node, left: Type, right: Type, operands: str) -> Type:
        if left.kind != right.kind:
            message = f"{operands} differ in kind: {left} and {right}"
            raise self.error("type_mismatch", node, message)
        if left.dimension != right.dimension:
            message = f"{operands} differ in dimension: {left} and {right}"
            raise self.error("dimension_mismatch", node, message)
        return left


def _is_zero(node: Node) -> bool:
    """A number literal of value zero, however written (0, 00, 0.0)."""
    return isinstance(node, Number) and set(node.text) <= {"0", "."}


def _location(text: str, span: Span, **owner) -> ExpressionLocation:
    """The span on its start line; a span that runs on ends with that line."""
    line = text.split("\n")[span.start_line - 1]
    end = span.end_column if span.end_line == span.start_line else len(line) + 1
    fragment = line[span.start_column - 1 : end - 1]
    return ExpressionLocation(
        span.start_line, span.start_column, end, fragment, **owner
    )


def _error(code: str, message: str, node: Node, text: str, **owner) -> RuleSetError:
    return RuleSetError(Diagnostic(code, message, _location(text, node.span, **owner)))
