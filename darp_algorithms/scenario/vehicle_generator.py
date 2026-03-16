from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from darp_algorithms.domain.location import Location
from darp_algorithms.domain.vehicle import Vehicle

from .scenario_config import ScenarioConfig


@dataclass
class VehicleGenerator:
    """
    Generiert auf Basis der ScenarioConfig eine Menge von Fahrzeugen
    """
    scenario_config: ScenarioConfig

    def generate_vehicles(self) -> list[Vehicle]:
        if self.scenario_config.number_of_vehicles < 0:
            raise ValueError("Die Anzahl der Fahrzeuge darf nicht negativ sein!")

        depot = Location(
            lat=self.scenario_config.depot_location_lat,
            lon=self.scenario_config.depot_location_lon,
            matrix_node_id=None,
            id=uuid4(),
        )

        vehicles: list[Vehicle] = []

        for _ in range(self.scenario_config.number_of_vehicles):
            vehicles.append(
                Vehicle(
                    start_position=depot,
                    start_time=self.scenario_config.scenario_start_time,
                    id=uuid4(),
                )
            )

        return vehicles
