from dataclasses import dataclass

from .vehicle import Vehicle
from .stop import Stop


@dataclass
class Route:
    """
    Domain-Klasse zur Repräsentation einer Route.

    Enthält das zugehörige Fahrzeug sowie die zugewiesenen Stopps innerhalb einer Route.
    """

    vehicle: Vehicle
    stops: list[Stop]
