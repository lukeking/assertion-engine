"""Tree images of checked rules (FR-014, research.md Decision 8).

layout places every node of a tree: leaves left to right in source order at
x = 0, 1, 2, ..., a parent at the mean of its children's x, and each node at
its depth below the root, which decides its height. label gives a node's
kind, source fragment and checked type, and for a Name what it resolved to.
render draws both on a Matplotlib Agg canvas and writes the PNG
(contracts/cli.md "assertion-rules tree").

A node's children are read from its fields, a tuple of arguments included,
so the temporal kinds need no case of their own; they are ordered by where
their spans start, not by the order of the fields.
"""

import os
import tempfile
from dataclasses import fields
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from assertion_engine.dsl.checker import Annotations
from assertion_engine.dsl.syntax import Name, Node, Span

_LEAF_WIDTH = 1.8  # inches from one leaf to the next
_LEVEL_HEIGHT = 1.1  # inches from one depth to the next


def layout(tree: Node) -> dict[int, tuple[float, int]]:
    """Each node's (x, depth) keyed by node identity; the root's depth is 0."""
    positions: dict[int, tuple[float, int]] = {}
    leaves = 0

    def place(node: Node, depth: int) -> float:
        nonlocal leaves
        below = _children(node)
        if below:
            x = sum(place(child, depth + 1) for child in below) / len(below)
        else:
            x = float(leaves)
            leaves += 1
        positions[id(node)] = (x, depth)
        return x

    place(tree, 0)
    return positions


def label(node: Node, annotations: Annotations, expression: str) -> str:
    """Kind, source fragment and type, one per line; a Name adds its resolution.

    expression is the text the tree was parsed from; a fragment that crosses a
    line break reads as one line, each run of whitespace collapsed to a space.
    """
    lines = [
        type(node).__name__,
        _fragment(node.span, expression),
        str(annotations.type_of(node)),
    ]
    if isinstance(node, Name):
        lines.append(annotations.resolution_of(node))
    return "\n".join(lines)


def render(expression: str, annotations: Annotations, output: Path) -> None:
    """Write the image of annotations.tree, parsed from expression, to output.

    The PNG goes to a staging file in output's directory, which is then
    hard-linked as output: unlike a rename, a link never replaces an existing
    file (FileExistsError), and no check-then-write gap lets one appear. The
    staging file is removed whether or not that succeeds.
    """
    tree = annotations.tree
    positions = layout(tree)
    columns = max(x for x, _ in positions.values()) + 1  # the last leaf is rightmost
    levels = max(depth for _, depth in positions.values()) + 1
    figure = Figure(figsize=(columns * _LEAF_WIDTH, levels * _LEVEL_HEIGHT))
    FigureCanvasAgg(figure)
    axes = figure.add_axes((0, 0, 1, 1))
    axes.set_axis_off()
    axes.set_xlim(-0.5, columns - 0.5)
    axes.set_ylim(0.5 - levels, 0.5)
    _draw(axes, tree, positions, annotations, expression)
    descriptor, name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".png", dir=output.parent
    )
    staging = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            # Labels may reach past the axes; the tight box keeps them whole.
            figure.savefig(handle, format="png", dpi=150, bbox_inches="tight")
        os.link(staging, output)
    finally:
        staging.unlink()


def _children(node: Node) -> list[Node]:
    found = []
    for field in fields(node):
        value = getattr(node, field.name)
        if isinstance(value, tuple):
            found.extend(value)
        elif not isinstance(value, (str, Span)):
            found.append(value)
    return sorted(
        found, key=lambda child: (child.span.start_line, child.span.start_column)
    )


def _fragment(span: Span, expression: str) -> str:
    lines = expression.split("\n")[span.start_line - 1 : span.end_line]
    # Cut the end first: on a one-line span, cutting the start would shift it.
    lines[-1] = lines[-1][: span.end_column - 1]
    lines[0] = lines[0][span.start_column - 1 :]
    return " ".join(" ".join(lines).split())


def _draw(
    axes: Axes,
    node: Node,
    positions: dict[int, tuple[float, int]],
    annotations: Annotations,
    expression: str,
) -> None:
    """Draw node above the edges to its children, then each child's subtree."""
    x, depth = positions[id(node)]
    for child in _children(node):
        child_x, child_depth = positions[id(child)]
        axes.plot((x, child_x), (-depth, -child_depth), color="0.6", zorder=1)
        _draw(axes, child, positions, annotations, expression)
    axes.text(
        x,
        -depth,
        label(node, annotations, expression),
        ha="center",
        va="center",
        family="monospace",
        fontsize=8,
        zorder=2,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "0.4"},
    )
