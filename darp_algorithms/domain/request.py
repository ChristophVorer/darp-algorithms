from __future__ import annotations
from .location import Location
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Request:
    """
    Domain-Klasse zur Repräsentation einer Anfrage.

    Enthält den Abhol- und Zielort, die Anzahl der Passagiere sowie den gewünschten Abholort einer Anfrage.
    """

    pickup: Location
    delivery: Location
    passengers: int
    desired_pickup_time: datetime
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.passengers <= 0:
            raise ValueError(f"Die Anzahl der Passagiere befindet sich außer des Wertebereichs: {self.passengers}")
