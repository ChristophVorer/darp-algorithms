from __future__ import annotations

from datetime import datetime
from math import isclose
from uuid import uuid4

import pytest

from darp_algorithms.domain.location import Location
from darp_algorithms.scenario.request_generator import RequestGenerator
from darp_algorithms.scenario.scenario_config import ScenarioConfig


def create_scenario_config(
        *,
        random_seed: int = 1234,
        number_of_requests: int = 20,
        number_of_vehicles: int = 2,
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


def request_information(request) -> tuple:
    """
    Definiert ein Tupel mit allen relevanten Informationen. Rundet die float Werte, um float-Ungenauigkeiten bei den
    Asserts zu vermeiden.
    """

    return (
        round(request.pickup.lat, 8),
        round(request.pickup.lon, 8),
        round(request.delivery.lat, 8),
        round(request.delivery.lon, 8),
        request.passengers,
        request.desired_pickup_time,
    )


def test_generate_requests_returns_expected_number_of_requests():
    """
    Testet, ob `generate_requests` die erwartete Anzahl an Anfragen generiert.
    """

    config = create_scenario_config(number_of_requests=7)
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    assert len(requests) == 7


def test_generate_requests_generates_same_requests_for_same_seed():
    """
    Testet, ob verschiedene Generator-Instanzen bei gleichem Random-Seed dieselben Anfragen erzeugen.
    """

    config = create_scenario_config(random_seed=1234)

    generator_1 = RequestGenerator(scenario_config=config)
    generator_2 = RequestGenerator(scenario_config=config)

    requests_1 = generator_1.generate_requests()
    requests_2 = generator_2.generate_requests()

    signatures_1 = [request_information(request) for request in requests_1]
    signatures_2 = [request_information(request) for request in requests_2]

    assert signatures_1 == signatures_2


def test_generate_requests_generates_different_requests_for_different_seeds():
    """
    Testet, ob verschiedene Generator-Instanzen bei unterschiedlichen Random-Seed unterschiedliche Anfragen erzeugen.
    """

    config_1 = create_scenario_config(random_seed=1234)
    config_2 = create_scenario_config(random_seed=5678)

    generator_1 = RequestGenerator(scenario_config=config_1)
    generator_2 = RequestGenerator(scenario_config=config_2)

    requests_1 = generator_1.generate_requests()
    requests_2 = generator_2.generate_requests()

    signatures_1 = [request_information(request) for request in requests_1]
    signatures_2 = [request_information(request) for request in requests_2]

    assert signatures_1 != signatures_2


def test_generate_requests_generates_locations_within_bounding_box():
    """
    Testet, ob `generate_requests` Anfragen innerhalb der Bounding-Box erzeugt.
    """

    config = create_scenario_config(
        min_lat=51.90,
        max_lat=51.95,
        min_lon=7.60,
        max_lon=7.65,
    )
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    for request in requests:
        assert config.min_lat <= request.pickup.lat <= config.max_lat
        assert config.min_lon <= request.pickup.lon <= config.max_lon
        assert config.min_lat <= request.delivery.lat <= config.max_lat
        assert config.min_lon <= request.delivery.lon <= config.max_lon


def test_generate_requests_respects_passenger_bounds():
    """
    Testet, ob `generate_requests` die maximale und minimale Passagierzahl aus der ScenarioConfig berücksichtigt.
    """

    config = create_scenario_config(
        min_passengers=2,
        max_passengers=2,
    )
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    assert len(requests) == 20
    assert all(request.passengers == 2 for request in requests)


def test_generate_requests_generates_request_service_time_window():
    """
    Testet, ob `generate_requests` Anfragen innerhalb des Service-Zeitraums aus der ScenarioConfig erzeugt.
    """

    start_time = datetime(2026, 3, 5, 9, 0, 0)
    end_time = datetime(2026, 3, 5, 12, 0, 0)

    config = create_scenario_config(
        scenario_start_time=start_time,
        scenario_end_time=end_time,
    )
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    for request in requests:
        assert start_time <= request.desired_pickup_time <= end_time


def test_generate_requests_generates_requests_within_distance_bounds():
    """
    Testet, ob `generate_requests` Anfragen erzeugt, die innerhalb der minimalen und maximalen Distanz für Abhol- und
    Zielknoten aus der ScenarioConfig liegen.
    """

    config = create_scenario_config(
        min_direct_distance_km=1.0,
        max_direct_distance_km=3.0,
    )
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    for request in requests:
        direct_distance = generator._approx_distance_km(request.pickup, request.delivery)
        assert config.min_direct_distance_km <= direct_distance <= config.max_direct_distance_km


def test_generate_requests_generates_requests_with_unique_ids():
    """
    Testet, ob `generate_requests` Anfragen mit eindeutigen Ids erzeugt.
    """

    config = create_scenario_config()
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    request_ids = [request.id for request in requests]
    assert len(request_ids) == len(set(request_ids))


def test_generate_requests_generates_locations_with_ids():
    """
    Testet, ob `generate_requests` jeder Location eine Id zuweist.
    """

    config = create_scenario_config()
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    for request in requests:
        assert request.pickup.id is not None
        assert request.delivery.id is not None


def test_generate_requests_generates_locations_without_matrix_node_ids():
    """
    Testet, ob `generate_requests` Locations ohne `matrix_node_id` erzeugt.
    """

    config = create_scenario_config()
    generator = RequestGenerator(scenario_config=config)

    requests = generator.generate_requests()

    for request in requests:
        assert request.pickup.matrix_node_id is None
        assert request.delivery.matrix_node_id is None


def test_generate_requests_raises_value_error_on_negative_number_of_requests():
    """
    Testet, ob `generate_requests` bei einer negativen Anzahl von Anfragen einen entsprechenden `ValueError` wirft.
    """

    config = create_scenario_config(number_of_requests=-1)
    generator = RequestGenerator(scenario_config=config)

    with pytest.raises(ValueError, match="Anzahl der Anfragen"):
        generator.generate_requests()


def test_random_pickup_time_raises_value_error_on_invalid_scenario_time_window():
    """
    Testet, ob `_random_pickup_time` bei einem nicht zulässigen Szenario-Zeitraum einen entsprechenden `ValueError`
    wirft.
    """

    config = create_scenario_config(
        scenario_start_time=datetime(2026, 3, 5, 16, 0, 0),
        scenario_end_time=datetime(2026, 3, 5, 8, 0, 0),
    )
    generator = RequestGenerator(scenario_config=config)

    with pytest.raises(ValueError, match="Startzeit.*vor.*Endzeit"):
        generator._random_pickup_time()


def test_generate_single_request_raises_value_error_if_no_valid_request_can_be_generated():
    """
    Testet, ob `_generate_single_request` einen entsprechenden `ValueError` wirft, sofern durch die zugrunde liegende
    ScenarioConfig keine Anfragen generiert werden können. In dem Fall dadurch dass die Mindest-Distanz zu hoch für
    die Bounding-Box ist.
    """

    config = create_scenario_config(
        number_of_requests=1,
        min_lat=51.90,
        max_lat=51.90001,
        min_lon=7.60,
        max_lon=7.60001,
        min_direct_distance_km=10.0,
        max_direct_distance_km=20.0,
    )
    generator = RequestGenerator(scenario_config=config)

    with pytest.raises(ValueError, match="valide Anfrage.*Distanzgrenzen"):
        generator._generate_single_request()


def test_approx_distance_km_is_zero_for_identical_locations():
    """
    Testet, ob `_approx_distance_km` 0 zurückgibt, sofern die Längen- und Breitengrade übereinstimmen.
    """

    location = Location(
        lat=51.96,
        lon=7.63,
        matrix_node_id=None,
        id=uuid4(),
    )

    distance = RequestGenerator._approx_distance_km(location, location)

    assert isclose(distance, 0.0, abs_tol=1e-9)


def test_approx_distance_km_is_symmetric():
    """
    Testet, ob `_approx_distance_km` symmetrische Distanzen zurückgibt, also für die Distanzen gilt:

    A -> B == B ->
    """

    location_a = Location(
        lat=51.96,
        lon=7.63,
        matrix_node_id=None,
        id=uuid4(),
    )
    location_b = Location(
        lat=51.97,
        lon=7.64,
        matrix_node_id=None,
        id=uuid4(),
    )

    distance_ab = RequestGenerator._approx_distance_km(location_a, location_b)
    distance_ba = RequestGenerator._approx_distance_km(location_b, location_a)

    assert isclose(distance_ab, distance_ba, rel_tol=1e-12, abs_tol=1e-12)
    assert distance_ab > 0.0
