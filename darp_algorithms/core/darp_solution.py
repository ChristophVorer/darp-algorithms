from dataclasses import dataclass

from .darp_instance import DarpInstance
from darp_algorithms.domain.route import Route

from uuid import UUID


@dataclass(frozen=True)
class DarpSolution:
    darp_instance: DarpInstance
    routes: list[Route]
    served_requests: list[UUID]
    unserved_requests: list[UUID]
