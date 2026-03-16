from __future__ import annotations

from .location import Location
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Vehicle:
    """
    Ein Fahrzeug, welches für die Bearbeitung von Anfragen zustaendig ist.
    """
    start_position: Location
    start_time: datetime
    id: UUID = field(default_factory=uuid4)