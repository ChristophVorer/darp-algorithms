from __future__ import annotations

from datetime import datetime
from datetime import timedelta

from darp_algorithms.core.darp_config import DarpConfig
from darp_algorithms.infrastructure import OsrmMatrixProvider
from darp_algorithms.infrastructure.darp_instance_generator import DarpInstanceGenerator
from darp_algorithms.domain.location import Location
from darp_algorithms.domain.request import Request
from darp_algorithms.domain.vehicle import Vehicle

from darp_algorithms.infrastructure.osrm_matrix_provider import MatrixData


class FakeOsrmMatrixProvider(OsrmMatrixProvider):
    """
    Fake-Klasse, die das Verhalten des OsrmMatrixProvider simuliert.
    """

    def __init__(self):
        super().__init__()
        # Hält die Liste an Locations und damit ihre Reihenfolge fest, die an den OsrmMatrixProvider übergeben wird,
        # fest
        self.locations_passed_to_build_matrices = None

        # Hält die Zeitmatrix, die an den OsrmMatrixProvider übergeben wird, fest
        self.build_travel_time_fn_called_with = None

        # Hält die Distanzmatrix, die an den OsrmMatrixProvider übergeben wird, fest
        self.build_travel_distance_fn_called_with = None

    def build_matrices(self, ordered_locations):
        """
        Baut zu Testzwecken die Matrizen mit linear ansteigenden Zeiten und Distanzen.
        """
        self.locations_passed_to_build_matrices = ordered_locations
        size = len(ordered_locations)
        return MatrixData(
            time_matrix_seconds=[[0] * size for _ in range(size)],
            distance_matrix_kilometers=[[0.0] * size for _ in range(size)],
        )

    def build_travel_time_fn(self, matrix_data):
        self.build_travel_time_fn_called_with = matrix_data
        return lambda a, b: timedelta(
            seconds=matrix_data.time_matrix_seconds[a.matrix_node_id][b.matrix_node_id]
        )

    def build_travel_distance_fn(self, matrix_data):
        self.build_travel_distance_fn_called_with = matrix_data
        return lambda a, b: matrix_data.distance_matrix_kilometers[a.matrix_node_id][b.matrix_node_id]


def test_remap_locations_for_matrix_assigns_consecutive_matrix_node_ids():
    """
    Testet, ob `remap_locations_for_matrix` aufeinanderfolgende `matrix_node_ids` für die Locations verteilt
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=51.95, lon=7.62)
    pickup = Location(lat=51.96, lon=7.63)
    delivery = Location(lat=51.97, lon=7.64)

    request = Request(
        pickup,
        delivery,
        desired_pickup_time=start_time,
        passengers=1
    )

    vehicle = Vehicle(
        depot,
        start_time=start_time
    )

    ordered_locations, remapped_vehicles, remapped_requests = (
        DarpInstanceGenerator.remap_locations_for_matrix(
            vehicles=[vehicle],
            requests=[request],
        )
    )

    assert len(ordered_locations) == 3
    assert [location.matrix_node_id for location in ordered_locations] == [0, 1, 2]

    assert remapped_vehicles[0].start_position.matrix_node_id == 0
    assert remapped_requests[0].pickup.matrix_node_id == 1
    assert remapped_requests[0].delivery.matrix_node_id == 2


def test_remap_locations_for_matrix_with_coordinate_duplicate():
    """
    Testet, ob `remap_locations_for_matrix` identische Koordinaten auf dieselbe `matrix_node_id` mappt.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    shared_location = Location(lat=51.96, lon=7.63)
    delivery = Location(lat=51.97, lon=7.64)

    request = Request(
        pickup=shared_location,
        delivery=delivery,
        desired_pickup_time=start_time,
        passengers=1
    )

    vehicle = Vehicle(
        shared_location,
        start_time=start_time
    )

    ordered_locations, remapped_vehicles, remapped_requests = (
        DarpInstanceGenerator.remap_locations_for_matrix(
            vehicles=[vehicle],
            requests=[request],
        )
    )

    assert len(ordered_locations) == 2

    assert remapped_vehicles[0].start_position is remapped_requests[0].pickup
    assert remapped_vehicles[0].start_position.matrix_node_id == 0
    assert remapped_requests[0].delivery.matrix_node_id == 1


def test_remap_locations_for_matrix_with_coordinate_duplicate_across_requests():
    """
    Testet, ob `remap_locations_for_matrix` identische Koordinaten auf dieselbe `matrix_node_id` mappt.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=51.95, lon=7.62)
    pickup = Location(lat=51.96, lon=7.63)
    delivery = Location(lat=51.97, lon=7.64)

    request_1 = Request(
        pickup=pickup,
        delivery=delivery,
        desired_pickup_time=start_time,
        passengers=1
    )
    request_2 = Request(
        pickup=pickup,
        delivery=delivery,
        desired_pickup_time=start_time + timedelta(minutes=5),
        passengers=1
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    ordered_locations, _, remapped_requests = DarpInstanceGenerator.remap_locations_for_matrix(
        vehicles=[vehicle],
        requests=[request_1, request_2],
    )

    assert len(ordered_locations) == 4
    assert remapped_requests[0].pickup is remapped_requests[1].pickup
    assert remapped_requests[0].pickup.matrix_node_id == 1
    assert remapped_requests[0].delivery.matrix_node_id == 2
    assert remapped_requests[1].delivery.matrix_node_id == 3


def test_remap_locations_for_matrix_preserves_request_and_vehicle_data():
    """
    Testet, ob `remap_locations_for_matrix` die verbleibenden Daten der Objekte behält.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=51.95, lon=7.62)
    pickup = Location(lat=51.96, lon=7.63)
    delivery = Location(lat=51.97, lon=7.64)

    request = Request(
        pickup=pickup,
        delivery=delivery,
        desired_pickup_time=start_time + timedelta(minutes=15),
        passengers=2,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    _, remapped_vehicles, remapped_requests = DarpInstanceGenerator.remap_locations_for_matrix(
        vehicles=[vehicle],
        requests=[request],
    )

    remapped_vehicle = remapped_vehicles[0]
    remapped_request = remapped_requests[0]

    assert remapped_vehicle.id == vehicle.id
    assert remapped_vehicle.start_time == vehicle.start_time

    assert remapped_request.id == request.id
    assert remapped_request.passengers == request.passengers
    assert remapped_request.desired_pickup_time == request.desired_pickup_time


def test_remap_locations_for_empty_request_and_vehicle_lists():
    """
    Testet, ob `remap_locations_for_matrix` für eine leere Anfrage- und Fahrzeugmenge eine leere Menge von Locations,
    Vehicles und Requests zurückgibt.
    """
    ordered_locations, remapped_vehicles, remapped_requests = (
        DarpInstanceGenerator.remap_locations_for_matrix(
            vehicles=[],
            requests=[],
        )
    )

    assert ordered_locations == []
    assert remapped_vehicles == []
    assert remapped_requests == []


def test_generate_instance_creates_complete_darp_instance():
    """
    Testet, ob `generate_instance` eine komplette DarpInstance generiert.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=51.95, lon=7.62)
    pickup_1 = Location(lat=51.96, lon=7.63)
    delivery_1 = Location(lat=51.97, lon=7.64)
    pickup_2 = Location(lat=51.98, lon=7.65)
    delivery_2 = Location(lat=51.99, lon=7.66)

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        desired_pickup_time=start_time,
        passengers=1
    )
    request_2 = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        desired_pickup_time=start_time + timedelta(minutes=10),
        passengers=1
    )

    generator = DarpInstanceGenerator(
        osrm_matrix_provider=FakeOsrmMatrixProvider()
    )

    darp_config = DarpConfig(
        vehicle_capacity=4
    )

    darp_instance = generator.generate_instance(
        darp_config=darp_config,
        vehicles=[vehicle],
        requests=[request_1, request_2],
    )

    assert darp_instance.darp_config is darp_config
    assert len(darp_instance.vehicles) == 1
    assert len(darp_instance.requests) == 2
    assert darp_instance.request_order == [request_1.id, request_2.id]

    assert set(darp_instance.requests.keys()) == {request_1.id, request_2.id}
    assert darp_instance.requests[request_1.id].id == request_1.id
    assert darp_instance.requests[request_2.id].id == request_2.id


def test_generate_instance_calls_osrm_provider_with_ordered_locations():
    """
    Testet, ob `generate_instance` den OSRM-Provider die Reihenfolge der Locations konserviert.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=51.95, lon=7.62)
    pickup = Location(lat=51.96, lon=7.63)
    delivery = Location(lat=51.97, lon=7.64)

    request = Request(
        pickup=pickup,
        delivery=delivery,
        desired_pickup_time=start_time,
        passengers=1,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    generator = DarpInstanceGenerator(
        osrm_matrix_provider=FakeOsrmMatrixProvider()
    )

    darp_config = DarpConfig(
        vehicle_capacity=4
    )

    darp_instance = generator.generate_instance(
        darp_config=darp_config,
        vehicles=[vehicle],
        requests=[request],
    )

    locations_passed_to_build_matrices = fake_provider.locations_passed_to_build_matrices
    assert locations_passed_to_build_matrices is not None
    assert len(locations_passed_to_build_matrices) == 3
    assert [location.matrix_node_id for location in locations_passed_to_build_matrices] == [0, 1, 2]

    assert fake_provider.build_travel_time_fn_called_with is not None
    assert fake_provider.build_travel_distance_fn_called_with is not None

    assert len(darp_instance.vehicles) == 1


def test_generate_instance_provides_sound_travel_functions():
    """
    Testet, ob `generate_instance` die Zeit- und Distanzmatrix aus dem OsrmMatrixProvider korrekt zurückgibt.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=51.95, lon=7.62)
    pickup = Location(lat=51.96, lon=7.63)
    delivery = Location(lat=51.97, lon=7.64)

    request = Request(
        pickup=pickup,
        delivery=delivery,
        desired_pickup_time=start_time,
        passengers=1,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    class FakeOsrmMatrixProviderWithCustomMatrices(FakeOsrmMatrixProvider):
        """
        FakeOsrmMatrixProvider mit expliziten Matrizen
        """

        def build_matrices(self, ordered_locations):
            self.locations_passed_to_build_matrices = ordered_locations
            return MatrixData(
                time_matrix_seconds=[
                    [0, 120, 240],
                    [120, 0, 360],
                    [240, 360, 0],
                ],
                distance_matrix_kilometers=[
                    [0.0, 1.2, 2.4],
                    [1.2, 0.0, 3.6],
                    [2.4, 3.6, 0.0],
                ],
            )

    generator = DarpInstanceGenerator(
        osrm_matrix_provider=FakeOsrmMatrixProviderWithCustomMatrices()
    )

    darp_config = DarpConfig(
        vehicle_capacity=4
    )

    darp_instance = generator.generate_instance(
        darp_config=darp_config,
        vehicles=[vehicle],
        requests=[request],
    )

    remapped_vehicle = darp_instance.vehicles[0]
    remapped_request = darp_instance.requests[request.id]

    assert (
            darp_instance.travel_time(remapped_vehicle.start_position, remapped_request.pickup)
            ==
            timedelta(seconds=120)
    )
    assert (
            darp_instance.travel_distance(remapped_request.pickup, remapped_request.delivery)
            ==
            3.6
    )


def test_generate_instance_uses_remapped_locations():
    """
    Testet, ob die Instanz, die durch `generate_instance` generiert wurde, die "remappten" Locations des
    DarpInstanceGenerators verwendet.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    shared_location = Location(lat=51.95, lon=7.62)
    delivery = Location(lat=51.97, lon=7.64)

    request = Request(
        pickup=shared_location,
        delivery=delivery,
        desired_pickup_time=start_time,
        passengers=1,
    )

    vehicle = Vehicle(
        start_position=shared_location,
        start_time=start_time
    )

    generator = DarpInstanceGenerator(
        osrm_matrix_provider=FakeOsrmMatrixProvider()
    )

    darp_config = DarpConfig(
        vehicle_capacity=4
    )

    darp_instance = generator.generate_instance(
        darp_config=darp_config,
        vehicles=[vehicle],
        requests=[request],
    )

    remapped_vehicle = darp_instance.vehicles[0]
    remapped_request = darp_instance.requests[request.id]

    assert remapped_vehicle.start_position is remapped_request.pickup
    assert remapped_vehicle.start_position.matrix_node_id == 0
    assert remapped_request.delivery.matrix_node_id == 1


def test_generate_instance_preserves_request_order():
    """
    Testet, ob `generate_instance` die Anfrage-Reihenfolge aus der Eingabeliste behält.
    """
    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=51.95, lon=7.62)
    pickup_1 = Location(lat=51.96, lon=7.63)
    delivery_1 = Location(lat=51.97, lon=7.64)
    pickup_2 = Location(lat=51.98, lon=7.65)
    delivery_2 = Location(lat=51.99, lon=7.66)
    pickup_3 = Location(lat=52.0, lon=7.67)
    delivery_3 = Location(lat=52.01, lon=7.68)

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        desired_pickup_time=start_time + timedelta(minutes=15),
        passengers=1,
    )
    request_2 = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        desired_pickup_time=start_time,
        passengers=1,
    )
    request_3 = Request(
        pickup=pickup_3,
        delivery=delivery_3,
        desired_pickup_time=start_time + timedelta(minutes=30),
        passengers=1,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    generator = DarpInstanceGenerator(
        osrm_matrix_provider=FakeOsrmMatrixProvider()
    )

    darp_config = DarpConfig(
        vehicle_capacity=4
    )

    darp_instance = generator.generate_instance(
        darp_config=darp_config,
        vehicles=[vehicle],
        requests=[request_2, request_1, request_3],
    )

    assert darp_instance.request_order == [request_2.id, request_1.id, request_3.id]
