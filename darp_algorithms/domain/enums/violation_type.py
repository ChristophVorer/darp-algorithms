from __future__ import annotations

from enum import Enum

class ViolationType(str, Enum):
    """
    Die Art einer Nebenbedingungsverletzung.
    """
    TIME_WINDOW = "time_window"
    CAPACITY = "capacity"
    DOUBLED_PICKUP = "doubled_pickup"
    PRECEDENCE = "precedence"
    MAX_RIDE_TIME = "max_ride_time"