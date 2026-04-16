from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional


@dataclass(frozen=True)
class ConstraintConfig:
    """
    Klasse, die die Konfigurationsmöglichkeiten und Parametrisierung der Nebenbedingungen kapselt
    """

    # De- bzw. Aktivierung der maximalen Fahrtzeitbeschränkung
    use_max_ride_time: bool = True

    # Max-Ride-Time-Faktor:
    # Wenn mrt_factor gesetzt ist, ergibt sich die Berechnung der maximalen Fahrtzeit aus:
    # "mrt_factor * direct_travel_time" (Max-Ride-Time-Faktor * direkte Fahrtzeit)
    mrt_factor: Optional[float] = 2.0

    # Optional kann auch eine konstante maximale Fahrtzeit über "fixed_max_ride_time" angegeben werden
    fixed_max_ride_time: Optional[timedelta] = None
