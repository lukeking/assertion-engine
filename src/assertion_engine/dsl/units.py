"""Dimensions and the declarable units (contracts/ruleset.md "Units and dimensions").

A dimension is three integer exponents over the base quantities length (m),
time (s) and battery percentage (%); % is a project base quantity, not SI's
dimensionless ratio (research.md Decision 4). Multiplying quantities adds
their exponents, dividing subtracts them. Only the six units of UNITS can be
declared; an inferred dimension may be any exponent triple.
"""

from dataclasses import dataclass
from types import MappingProxyType

_SYMBOLS = ("m", "s", "%")


@dataclass(frozen=True)
class Dimension:
    length: int = 0
    time: int = 0
    battery: int = 0

    def __mul__(self, other: Dimension) -> Dimension:
        return Dimension(
            self.length + other.length,
            self.time + other.time,
            self.battery + other.battery,
        )

    def __truediv__(self, other: Dimension) -> Dimension:
        return Dimension(
            self.length - other.length,
            self.time - other.time,
            self.battery - other.battery,
        )

    def __str__(self) -> str:
        """Label: positive exponents over a slash, bases in (m, s, %) order.

        The six declarable dimensions print as their unit; others read like
        m^2, 1/s, m/s^2 or 1/(s*%), a product under the slash in parentheses.
        """
        pairs = tuple(zip(_SYMBOLS, (self.length, self.time, self.battery)))
        numerator = [_power(symbol, power) for symbol, power in pairs if power > 0]
        denominator = [_power(symbol, -power) for symbol, power in pairs if power < 0]
        label = "*".join(numerator) or "1"
        if not denominator:
            return label
        if len(denominator) == 1:
            return f"{label}/{denominator[0]}"
        return f"{label}/({'*'.join(denominator)})"


def _power(symbol: str, power: int) -> str:
    return symbol if power == 1 else f"{symbol}^{power}"


UNITS = MappingProxyType(
    {
        "1": Dimension(0, 0, 0),
        "%": Dimension(0, 0, 1),
        "m": Dimension(1, 0, 0),
        "s": Dimension(0, 1, 0),
        "m/s": Dimension(1, -1, 0),
        "%/s": Dimension(0, -1, 1),
    }
)


def dimension_of(unit: str) -> Dimension:
    """Return a declarable unit's dimension; any other unit string is rejected."""
    if unit not in UNITS:
        raise ValueError(f"{unit!r} is not a declarable unit ({', '.join(UNITS)})")
    return UNITS[unit]
