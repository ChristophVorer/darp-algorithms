from dataclasses import dataclass

from .vehicle import Vehicle
from .stop import Stop

@dataclass
class Route:
    vehicle: Vehicle
    stops: list[Stop]