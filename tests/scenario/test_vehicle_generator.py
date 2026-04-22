from __future__ import annotations

from datetime import datetime

import pytest

from darp_algorithms.scenario.scenario_config import ScenarioConfig
from darp_algorithms.scenario.vehicle_generator import VehicleGenerator


def make_scenario_config(
        *,
        random_seed: int = 1234,
        number_of_requests: int = 5,
        number_of_vehicles: int = 5,
        scenario_start_time: datetime = datetime(2026, 3, 5, 8, 0, 0),
        scenario_end_time: datetime = datetime(2026, 3, 5, 16, 0, 0),
        min_passengers: int = 1,
        max_passengers: int = 3,
        min_lat: float = 51.86,
        max_lat: float = 52.04,
        min_lon: float = 7.53,
        max_lon: float = 7.76,
        depot_location_lat: float = 51.9566,
        depot_location_lon: float = 7.6377,
        min_direct_distance_km: float = 0.5,
        max_direct_distance_km: float = 15.0,
) -> ScenarioConfig:
    return ScenarioConfig(
        random_seed=random_seed,
        number_of_requests=number_of_requests,
        number_of_vehicles=number_of_vehicles,
        scenario_start_time=scenario_start_time,
        scenario_end_time=scenario_end_time,
        min_passengers=min_passengers,
        max_passengers=max_passengers,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        depot_location_lat=depot_location_lat,
        depot_location_lon=depot_location_lon,
        min_direct_distance_km=min_direct_distance_km,
        max_direct_distance_km=max_direct_distance_km,
    )


def test_generate_vehicles_generates_requested_number_of_vehicles():
    """
    Testet, ob `generate_vehicles` die übergebene Anzahl von Anfragen generiert.
    """

    config = make_scenario_config(number_of_vehicles=4)
    generator = VehicleGenerator(scenario_config=config)

    vehicles = generator.generate_vehicles()

    assert len(vehicles) == 4


def test_generate_vehicles_returns_empty_list_for_zero_vehicles():
    """
    Testet, ob `generate_vehicles` für ScenarioConfig mit 0 angefragten Fahrzeugen eine leere Menge von Fahrzeugen
    generiert.
    """

    config = make_scenario_config(number_of_vehicles=0)
    generator = VehicleGenerator(scenario_config=config)

    vehicles = generator.generate_vehicles()

    assert vehicles == []


def test_generate_vehicles_generates_vehicle_with_identical_start_time():
    """
    Testet, ob `generate_vehicles` dieselbe Startzeit für alle erzeugten Fahrzeugen setzt.
    """

    start_time = datetime(2026, 3, 5, 9, 30, 0)

    config = make_scenario_config(scenario_start_time=start_time)
    generator = VehicleGenerator(scenario_config=config)

    vehicles = generator.generate_vehicles()

    assert all(vehicle.start_time == start_time for vehicle in vehicles)


def test_generate_vehicles_generates_vehicle_with_identical_start_position():
    """
    Testet, ob `generate_vehicles` dieselbe Startposition für alle erzeugten Fahrzeugen setzt.
    """

    depot_lat = 51.9701
    depot_lon = 7.6012

    config = make_scenario_config(
        depot_location_lat=depot_lat,
        depot_location_lon=depot_lon,
    )
    generator = VehicleGenerator(scenario_config=config)

    vehicles = generator.generate_vehicles()

    for vehicle in vehicles:
        assert vehicle.start_position.lat == depot_lat
        assert vehicle.start_position.lon == depot_lon


def test_generate_vehicles_assigns_unique_ids():
    """
    Testet, ob `generate_vehicles` für jedes erzeugte Fahrzeug eine eindeutige Id setzt.
    """

    config = make_scenario_config()
    generator = VehicleGenerator(scenario_config=config)

    vehicles = generator.generate_vehicles()

    vehicle_ids = [vehicle.id for vehicle in vehicles]
    assert len(vehicle_ids) == len(set(vehicle_ids))


def test_generate_vehicles_sets_depot_id():
    """
    Testet, ob `generate_vehicles` der Startposition eine Id zuweist.
    """

    config = make_scenario_config()
    generator = VehicleGenerator(scenario_config=config)

    vehicles = generator.generate_vehicles()

    for vehicle in vehicles:
        assert vehicle.start_position.id is not None


def test_generate_vehicles_sets_no_start_position_matrix_node_id():
    """
    Testet, ob `generate_vehicles` der Startposition keine `matrix_node_id` zuweist.
    """

    config = make_scenario_config()
    generator = VehicleGenerator(scenario_config=config)

    vehicles = generator.generate_vehicles()

    for vehicle in vehicles:
        assert vehicle.start_position.matrix_node_id is None


def test_generate_vehicles_value_error_on_negative_number_of_vehicles():
    """
    Testet, ob `generate_vehicles` bei einer negativen Anzahl von Fahrzeugen einen entsprechenden ValueError wirft.
    """

    config = make_scenario_config(number_of_vehicles=-1)
    generator = VehicleGenerator(scenario_config=config)

    with pytest.raises(ValueError, match="Anzahl der Fahrzeug"):
        generator.generate_vehicles()
