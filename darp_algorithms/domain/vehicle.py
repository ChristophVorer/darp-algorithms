from __future__ import annotations

from .location import Location
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Vehicle:
    """
    Domain-Klasse zur Repräsentation eines Stopps.

    Enthält die Informationen über die Startposition sowie den Startzeitpunkt des Fahrzeugs.
    """

    start_position: Location
    start_time: datetime
    id: UUID = field(default_factory=uuid4)
