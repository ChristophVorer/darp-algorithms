from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .enums.stop_kind import StopKind
from .location import Location


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
