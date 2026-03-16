from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .darp_config import DarpConfig
from .route_state import TravelTimeFn, TravelDistanceFn
from darp_algorithms.domain.request import Request
from darp_algorithms.domain.vehicle import Vehicle


@dataclass(frozen=True)
class DarpInstance:
    darp_config: DarpConfig
    vehicles: list[Vehicle]
    requests: dict[UUID, Request]
    request_order: list[UUID]
    travel_time: TravelTimeFn
    travel_distance: TravelDistanceFn
