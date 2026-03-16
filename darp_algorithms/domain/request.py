from __future__ import annotations
from .location import Location
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass(frozen=True, slots=True)
class Request:
    """
    Eine DARP-Anfrage für eine Gruppe von Passagieren
    """
    pickup: Location
    delivery: Location
    passengers: int
    desired_pickup_time: datetime
    id: UUID = field(default_factory=uuid4)