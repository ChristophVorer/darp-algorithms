from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import uuid4

from darp_algorithms.domain.location import Location
from darp_algorithms.domain.request import Request

from .scenario_config import ScenarioConfig


@dataclass
class RequestGenerator:
    """
    Generiert auf Basis der ScenarioConfig eine Menge von Anfragen mit gleichverteilten Koordinaten für Abhol- und
    Zielknoten in einer Bounding-Box definiert durch einen minimalen/maximalen Längen- und Breitengrad.

    Standardmäßig wird dabei eine Bounding-Box um Münster herum gebildet (siehe ScenarioConfig)
    """

    scenario_config: ScenarioConfig
    random_generator: random.Random = field(init=False)

    def __post_init__(self) -> None:
        """
        Gibt ein Random-Objekt zur Generierung von Zufallswerten zurück.
        Das Random-Objekt wird mit dem Random-Seed aus der ScenarioConfig initialisiert.
        """

        self.random_generator = random.Random(self.scenario_config.random_seed)

    def generate_requests(self) -> list[Request]:
        """
        Generiert eine Menge von synthetischen Anfragen gemäß der ScenarioConfig, die an den DemandGenerator übergeben
        wurde.
        """

        if self.scenario_config.number_of_requests < 0:
            raise ValueError("Die Anzahl der Anfragen darf nicht negativ sein.")

        requests: list[Request] = []

        for _ in range(self.scenario_config.number_of_requests):
            request = self._generate_single_request()
            requests.append(request)

        return requests

    def _generate_single_request(self) -> Request:
        """
        Generiert eine einzelne synthetische Anfrage gemäß der ScenarioConfig, die an den DemandGenerator übergeben
        wurde.
        """

        for _ in range(100):
            # Es wird bis zu 100-mal versucht ein Koordinaten-Paar zu erstellen, dessen Distanz innerhalb der minimalen
            # und der maximalen Distanz liegt (siehe ScenarioConfig).
            pickup = self._random_location()
            delivery = self._random_location()

            direct_distance_km = self._approx_distance_km(pickup, delivery)

            if (
                    self.scenario_config.min_direct_distance_km
                    <= direct_distance_km
                    <= self.scenario_config.max_direct_distance_km
            ):
                return Request(
                    pickup=pickup,
                    delivery=delivery,
                    passengers=self.random_generator.randint(
                        self.scenario_config.min_passengers,
                        self.scenario_config.max_passengers,
                    ),
                    desired_pickup_time=self._random_pickup_time(),
                    id=uuid4(),
                )

        raise ValueError("Es konnte keine valide Anfrage innerhalb der Distanzgrenzen generiert werden.")

    def _random_location(self) -> Location:
        """
        Generiert eine zufällige Location innerhalb der definierten Bounding-Box aus der ScenarioConfig.

        uniform() sorgt dafür, dass die Koordinaten-Paare gleichverteilt innerhalb der Bounding-Box generiert werden.
        """

        return Location(
            lat=self.random_generator.uniform(self.scenario_config.min_lat, self.scenario_config.max_lat),
            lon=self.random_generator.uniform(self.scenario_config.min_lon, self.scenario_config.max_lon),
            matrix_node_id=None,
            id=uuid4(),
        )

    def _random_pickup_time(self) -> datetime:
        """
        Generiert einen zufälligen gewünschten Abholzeitpunkt für die Anfrage gemäß der ScenarioConfig.
        """

        # Maximal erlaubter Offset für den gewünschten Abholzeitpunkt nach dem Start des Szenarios
        max_offset = self.scenario_config.scenario_end_time - self.scenario_config.scenario_start_time
        max_offset_seconds = int(max_offset.total_seconds())

        if max_offset_seconds < 0:
            raise ValueError("Die Startzeit des Szenarios muss vor der Endzeit liegen!")

        # Zufällig generierter Offset für den gewünschten Abholzeitpunkt nach dem Start des Szenarios
        offset_seconds = self.random_generator.randint(0, max_offset_seconds)

        return self.scenario_config.scenario_start_time + timedelta(seconds=offset_seconds)

    @staticmethod
    def _approx_distance_km(a: Location, b: Location) -> float:
        """
        Einfache Approximation für den Luftlinienabstand zweier Locations

        Bewusste Abstraktion, um die Synthese von Anfragen möglichst simpel zu halten. Für die Routingbewertung wird im
        späteren Verlauf die OSRM-API genutzt, um die Distanzen und Zeiten zwischen den Locations realistisch zu
        berechnen.

        Quelle: https://www.movable-type.co.uk/scripts/latlong.html
        (Equirectangular approximation)
        """

        latitude_km = 111.0 * (a.lat - b.lat)
        mean_latitude_radians = math.radians((a.lat + b.lat) / 2.0)
        longitude_km = 111.0 * math.cos(mean_latitude_radians) * (a.lon - b.lon)

        return math.sqrt(latitude_km ** 2 + longitude_km ** 2)
