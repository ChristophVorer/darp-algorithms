from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional


@dataclass(frozen=True)
class ConstraintConfig:
    """
    Maximale Fahrtzeit Nebenbedingung
    """
    # Gibt an, ob das DARP eine maximale Fahrtzeitbeschränkung beinhalten soll
    use_max_ride_time: bool = True

    # Faktor für die maximale Fahrtzeit
    # Wenn mrt_factor gesetzt ist, ergibt sich die Berechnung der maximalen Fahrtzeit aus:
    # "mrt_factor * direct_travel_time" (MRT-Faktor * direkte Fahrtzeit)
    mrt_factor: Optional[float] = 2.0

    # Optional kann auch eine konstante maximale Fahrtzeit über "fixed_max_ride_time" angegeben werden
    fixed_max_ride_time: Optional[timedelta] = None
