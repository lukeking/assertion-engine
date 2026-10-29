"""The built-in, read-only names (contracts/ruleset.md "Built-in vocabulary").

Types are written as the contract tables write them: a kind (scalar or
vector) and a declarable unit (units.UNITS). Temporal keywords are not
vocabulary entries: the parser recognizes them and the checker knows their
signatures (data-model.md "Vocabulary").
"""

from types import MappingProxyType

# From the M0 telemetry snapshot; vehicle_id is not exposed.
FIELDS = MappingProxyType(
    {
        "sequence_number": ("scalar", "1"),
        "mission_time_s": ("scalar", "s"),
        "position_ned_m": ("vector", "m"),
        "velocity_ned_mps": ("vector", "m/s"),
        "battery_percent": ("scalar", "%"),
    }
)

# name -> (argument kinds, result kind); the result keeps its argument's
# dimension, so both read vector[D] -> scalar[D].
FUNCTIONS = MappingProxyType(
    {
        "norm": (("vector",), "scalar"),  # 3-D length
        "hnorm": (("vector",), "scalar"),  # horizontal length, sqrt(n^2 + e^2)
    }
)

# name -> (unit, DSL definition), parsed and checked like a rule set's own
# derived quantities.
BUILT_IN_DERIVED = MappingProxyType(
    {
        "altitude_m": ("m", "-position_ned_m.d"),
        "descent_speed_mps": ("m/s", "velocity_ned_mps.d"),
        "horizontal_speed_mps": ("m/s", "hnorm(velocity_ned_mps)"),
        "home_distance_m": ("m", "hnorm(position_ned_m)"),  # home is the NED origin
    }
)
