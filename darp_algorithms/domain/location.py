from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Location:
    """
    Koordinaten-Informationen eines Ortes für die OSRM-API Konvertierung
    """
    lat: float
    lon: float
    matrix_node_id: Optional[int] = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError(f"Breitengrad befindet sich außerhalb des Wertebereichs: {self.lat}")

        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError(f"Längengrad befindet sich außerhalb des Wertebereichs: {self.lon}")
