from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .darp_config import DarpConfig
from .route_state import TravelTimeFn, TravelDistanceFn
from darp_algorithms.domain.request import Request
from darp_algorithms.domain.vehicle import Vehicle


@dataclass(frozen=True)
class DarpInstance:
    """
    Definiert eine DARP-Instanz und enthält eine Menge von Fahrzeugen und Anfragen sowie deren Reihenfolge. Darüber
    hinaus enthält Sie die Funktionen zur Berechnung der Zeiten und Distanzen zwischen den Anfragen.
    """

    # Konfiguration des zugrundeliegenden DARPs
    darp_config: DarpConfig

    # Menge der Fahrzeuge
    vehicles: list[Vehicle]

    # Menge der Anfragen
    requests: dict[UUID, Request]

    # Reihenfolge der Anfragen:
    # Bestimmt insbesondere in Hinblick auf die Greedy-Verfahren die Abarbeitungsreihenfolge der Anfragen
    request_order: list[UUID]

    # Zeit- und Distanzfunktion
    travel_time: TravelTimeFn
    travel_distance: TravelDistanceFn
