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
- Previous: ("prev", value).
- Ago: ("ago", value, duration).
- HeldFor: ("held_for", condition, duration).
- Within: ("within", condition, duration).
- Slope: ("slope", value, window).
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
    "telemetry-heartbeat": (
        "<=",
        ("-", "mission_time_s", ("prev", "mission_time_s")),
        "heartbeat_max_s",
    ),
    "monotonic-sequence": (
        "and",
        (
            "==",
            "sequence_number",
            ("+", ("prev", "sequence_number"), ("number", "1")),
        ),
        (">", "mission_time_s", ("prev", "mission_time_s")),
    ),
    "battery-tier-low": (
        "implies",
        (
            "held_for",
            ("<", "battery_percent", "battery_low_percent"),
            "reaction_time_s",
        ),
        ("<", "home_distance_m", ("ago", "home_distance_m", "closing_window_s")),
    ),
    "battery-tier-critical": (
        "implies",
        (
            "held_for",
            ("<", "battery_percent", "battery_critical_percent"),
            "reaction_time_s",
        ),
        (">", "descent_speed_mps", ("number", "0")),
    ),
    "battery-tier-emergency": (
        "implies",
        ("<", "battery_percent", "battery_emergency_percent"),
        (
            "within",
            ("<", "altitude_m", "landed_altitude_m"),
            "landing_deadline_s",
        ),
    ),
    "no-sudden-jump": (
        "<=",
        (
            "/",
            ("call", "norm", ("-", "position_ned_m", ("prev", "position_ned_m"))),
            ("-", "mission_time_s", ("prev", "mission_time_s")),
        ),
        "jump_rate_max_mps",
    ),
    "battery-drain-rate": (
        "<=",
        ("neg", ("slope", "battery_percent", "drain_window_s")),
        "drain_rate_max_percent_per_s",
    ),
    "battery-runout-forecast": (
        ">=",
        (
            "/",
            ("-", "battery_percent", "battery_critical_percent"),
            ("neg", ("slope", "battery_percent", "trend_window_s")),
        ),
        "return_time_s",
    ),
    "altitude-trend-ceiling": (
        "<=",
        (
            "+",
            "altitude_m",
            ("*", ("slope", "altitude_m", "climb_window_s"), "lookahead_s"),
        ),
        "altitude_ceiling_m",
    ),
    "geofence-forecast": (
        "<=",
        (
            "call",
            "hnorm",
            ("+", "position_ned_m", ("*", "velocity_ned_mps", "lookahead_s")),
        ),
        "fence_radius_m",
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
