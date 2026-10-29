"""Hand-written expected tree shapes of corpus rules and derived definitions.

Each shape is read off the expression with contracts/grammar.ebnf, never taken
from parser output (plan.md "測試的獨立性"). Shapes leave out spans: unit tests
check spans by hand, and the golden files freeze them once the shapes match.

Notation, one form per node kind (contracts/syntax-tree.md "Node kinds"):

- Name: the bare name string, e.g. "battery_percent".
- Number: ("number", source text), e.g. ("number", "0.5").
- Arithmetic: (op, left, right), op one of "+" "-" "*" "/".
- Compare: (op, left, right), op one of "<" "<=" ">" ">=" "==" "!=".
- And: ("and", left, right).
- Implies: ("implies", antecedent, consequent).
- Conditional: ("if", condition, then, else).
- Negate: ("neg", operand).
- Component: (".", target, axis), axis one of "n" "e" "d".
- Call: ("call", function name, argument, ...).

The temporal kinds get their forms with the temporal and trend rules.
"""

RULE_SHAPES = {
    "battery-floor": (">=", "battery_percent", "battery_floor_percent"),
    "altitude-ceiling": ("<=", "altitude_m", "altitude_ceiling_m"),
    "horizontal-speed-limit": (
        "<=",
        "horizontal_speed_mps",
        "horizontal_speed_max_mps",
    ),
    "return-reserve": (
        ">",
        "battery_percent",
        (
            "+",
            ("*", "return_time_s", "drain_rate_percent_per_s"),
            "return_reserve_percent",
        ),
    ),
    "geofence-cylinder": (
        "and",
        ("<=", "home_distance_m", "fence_radius_m"),
        ("<=", "altitude_m", "fence_altitude_m"),
    ),
    "low-battery-stay-close": (
        "implies",
        ("<", "battery_percent", "battery_low_percent"),
        ("<=", "home_distance_m", "low_battery_radius_m"),
    ),
    "descent-speed-near-ground": (
        "<=",
        "descent_speed_mps",
        (
            "if",
            ("<", "altitude_m", "near_ground_altitude_m"),
            "near_ground_descent_max_mps",
            "descent_max_mps",
        ),
    ),
}

DERIVED_SHAPES = {
    "altitude_m": ("neg", (".", "position_ned_m", "d")),
    "descent_speed_mps": (".", "velocity_ned_mps", "d"),
    "horizontal_speed_mps": ("call", "hnorm", "velocity_ned_mps"),
    "home_distance_m": ("call", "hnorm", "position_ned_m"),
    "return_time_s": (
        "+",
        ("/", "home_distance_m", "cruise_speed_mps"),
        ("/", "altitude_m", "descent_rate_mps"),
    ),
}
