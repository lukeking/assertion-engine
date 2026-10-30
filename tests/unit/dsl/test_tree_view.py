"""FR-014, research.md Decision 8: tree-image layout, labels and PNG writing.

Positions and labels are written by hand from Decision 8; none is produced by
tree_view. Hand-built trees carry spans counted in the source text quoted
beside them. Every image goes to tmp_path.
"""

import pytest
from matplotlib.figure import Figure

from assertion_engine.dsl import load_ruleset
from assertion_engine.dsl.syntax import (
    Ago,
    Arithmetic,
    Call,
    Component,
    Name,
    Number,
    Previous,
    Span,
)
from assertion_engine.dsl.tree_view import label, layout, render

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# One rule whose names resolve to a field, a parameter and a derived quantity,
# written over two lines so fragments cross a line break. altitude_m>=0 has no
# spaces: a fragment cut one column late would show its neighbour.
RULE_SET = (
    'schema_version = "1.0.0"',
    "",
    "[parameters.battery_floor_percent]",
    'unit = "%"',
    "",
    "[rules.r]",
    'category = "logic"',
    'expression = """',
    "battery_percent >=",
    '  battery_floor_percent and altitude_m>=0"""',
)


def checked_rule():
    ruleset = load_ruleset(("\n".join(RULE_SET) + "\n").encode("utf-8"))
    return ruleset.rules["r"]


def at(start, end, line=1):
    return Span(line, start, line, end)


def test_FR014_parent_x_is_the_mean_of_its_children_and_depth_is_y():
    # a * b + c: c sits one level above a and b but comes after them.
    a, b, c = Name("a", at(1, 2)), Name("b", at(5, 6)), Name("c", at(9, 10))
    product = Arithmetic("*", a, b, at(1, 6))
    total = Arithmetic("+", product, c, at(1, 10))
    # The root is the mean of its children (0.5, 2), not of its leaves (0, 1, 2).
    assert layout(total) == {
        id(total): (1.25, 0),
        id(product): (0.5, 1),
        id(c): (2.0, 1),
        id(a): (0.0, 2),
        id(b): (1.0, 2),
    }


def test_FR014_leaves_follow_source_order_not_field_order():
    # Hand-built: the field listed first covers the later fragment of "a - b".
    a, b = Name("a", at(1, 2)), Name("b", at(5, 6))
    tree = Arithmetic("-", b, a, at(1, 6))
    assert layout(tree) == {id(tree): (0.5, 0), id(a): (0.0, 1), id(b): (1.0, 1)}


def test_FR014_layout_reads_children_from_any_node_fields():
    # f(p.d, v, 2): a tuple of arguments, and a Component's axis is no child.
    p = Name("p", at(3, 4))
    axis = Component(p, "d", at(3, 6))
    v, two = Name("v", at(8, 9)), Number("2", at(11, 12))
    call = Call("f", (axis, v, two), at(1, 13))
    assert layout(call) == {
        id(call): (1.0, 0),
        id(axis): (0.0, 1),
        id(p): (0.0, 2),
        id(v): (1.0, 1),
        id(two): (2.0, 1),
    }
    # prev(ago(w, 5)): temporal kinds need no case of their own.
    w, five = Name("w", at(10, 11)), Number("5", at(13, 14))
    ago = Ago(w, five, at(6, 15))
    previous = Previous(ago, at(1, 16))
    assert layout(previous) == {
        id(previous): (0.5, 0),
        id(ago): (0.5, 1),
        id(w): (0.0, 2),
        id(five): (1.0, 2),
    }


def test_FR014_label_shows_kind_fragment_type_and_name_resolution():
    rule = checked_rule()
    conjunction = rule.annotations.tree
    floor, ground = conjunction.left, conjunction.right

    def text(node):
        return label(node, rule.annotations, rule.expression)

    # A fragment that crosses a line break reads as one line, spaces collapsed.
    assert text(conjunction) == (
        "And\nbattery_percent >= battery_floor_percent and altitude_m>=0\nbool"
    )
    assert text(floor) == "Compare\nbattery_percent >= battery_floor_percent\nbool"
    assert text(floor.left) == "Name\nbattery_percent\nscalar[%]\nfield"
    assert text(floor.right) == "Name\nbattery_floor_percent\nscalar[%]\nparameter"
    assert text(ground) == "Compare\naltitude_m>=0\nbool"
    assert text(ground.left) == "Name\naltitude_m\nscalar[m]\nderived"
    assert text(ground.right) == "Number\n0\nscalar[m]"


def test_FR014_render_writes_a_png_and_nothing_else(tmp_path):
    rule = checked_rule()
    output = tmp_path / "r.png"
    render(rule.expression, rule.annotations, output)
    data = output.read_bytes()
    assert data.startswith(PNG_SIGNATURE)
    assert len(data) > len(PNG_SIGNATURE)
    assert list(tmp_path.iterdir()) == [output]


def test_FR014_render_refuses_an_existing_output_and_keeps_its_bytes(tmp_path):
    rule = checked_rule()
    output = tmp_path / "r.png"
    output.write_bytes(b"not mine")
    with pytest.raises(FileExistsError):
        render(rule.expression, rule.annotations, output)
    assert output.read_bytes() == b"not mine"
    assert list(tmp_path.iterdir()) == [output]


def test_FR014_failed_drawing_leaves_no_partial_file(tmp_path, monkeypatch):
    def broken_savefig(self, target, **kwargs):
        if hasattr(target, "write"):
            target.write(PNG_SIGNATURE)
        else:
            with open(target, "wb") as handle:
                handle.write(PNG_SIGNATURE)
        raise RuntimeError("drawing failed")

    monkeypatch.setattr(Figure, "savefig", broken_savefig)
    rule = checked_rule()
    with pytest.raises(RuntimeError, match="drawing failed"):
        render(rule.expression, rule.annotations, tmp_path / "r.png")
    assert list(tmp_path.iterdir()) == []
