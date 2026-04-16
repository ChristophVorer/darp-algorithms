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
    Domain-Klasse zur Repräsentation eines Stopps.

    Enthält die Informationen über die Art des Stopps (Abholung/Absetzung), die zugehörige Anfrage sowie den Ort des
    Stopps
    """

    kind: StopKind
    request_id: UUID
    location: Location
