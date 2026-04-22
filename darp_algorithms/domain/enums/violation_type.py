from __future__ import annotations

from enum import Enum


class ViolationType(str, Enum):
    """
    Definiert die Art einer Nebenbedingungsverletzung.
    """

    # Zeitfensterverletzung
    TIME_WINDOW = "time_window"

    # Kapazitätsverletzung
    CAPACITY = "capacity"

    # Doppelte Abholung
    DOUBLED_PICKUP = "doubled_pickup"

    # Verletzung der zulässigen Knotenfolge:
    # Tritt auf, wenn versucht wird einen Zielknoten vor einem Abholknoten einzufügen
    PRECEDENCE = "precedence"

    # Verletzung der maximalen Fahrtzeit
    MAX_RIDE_TIME = "max_ride_time"
