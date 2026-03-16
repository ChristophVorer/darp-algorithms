from __future__ import annotations

from .location import Location
from .enums.stop_kind import StopKind
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass(frozen=True, slots=True)
class Stop:
    """
    Ein Stopp assoziiert mit einer Route eines Fahrzeugs, einer entsprechenden Anfrage und der Art des Stopps (Abholung/Absetzung).
    """
    kind: StopKind
    request_id: UUID
    location: Location
    planned_time: Optional[datetime] = None