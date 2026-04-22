from __future__ import annotations
from unittest.mock import Mock

from datetime import datetime, timedelta
from uuid import UUID

from darp_algorithms.core import DarpSolution
from darp_algorithms.core.constraint_config import ConstraintConfig
from darp_algorithms.core.darp_config import DarpConfig
from darp_algorithms.core.darp_instance import DarpInstance
from darp_algorithms.core.greedy_heuristic import (
    greedy_construction_routes_with_order,
    best_insertion_for_request,
    greedy_construction_routes,
    sort_by_earliest_desired_pickup_time,
    greedy_construction_routes_time_restrictive_scenario,
)
from darp_algorithms.core.objective_config import ObjectiveConfig
from darp_algorithms.domain.enums.stop_kind import StopKind
from darp_algorithms.domain.location import Location
from darp_algorithms.domain.request import Request
from darp_algorithms.domain.route import Route
from darp_algorithms.domain.stop import Stop
from darp_algorithms.domain.vehicle import Vehicle


def travel_time_fn(matrix_seconds):
    def travel_time(a: Location, b: Location) -> timedelta:
        return timedelta(seconds=matrix_seconds[a.matrix_node_id][b.matrix_node_id])

    return travel_time


def travel_distance_fn(matrix_distances):
    def travel_distance(a: Location, b: Location) -> float:
        return matrix_distances[a.matrix_node_id][b.matrix_node_id]

    return travel_distance


def create_instance(
        *,
        vehicles: list[Vehicle],
        requests: list[Request],
        time_matrix: list[list[int]],
        distance_matrix: list[list[float]],
) -> DarpInstance:
    darp_config = DarpConfig(
        vehicle_capacity=4,
        objective_config=ObjectiveConfig(),
        constraint_config=ConstraintConfig(),
    )

    return DarpInstance(
        darp_config=darp_config,
        vehicles=vehicles,
        requests={request.id: request for request in requests},
        request_order=[request.id for request in requests],
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )


def test_sort_by_earliest_desired_pickup_time():
    """
    Testet die Funktion `sort_by_earliest_desired_pickup_time`
    """
    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    request_late = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),

    )

    request_middle = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=15),
    )

    request_early = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=5),
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    time_matrix = [[0] * 5 for _ in range(5)]
    distance_matrix = [[0.0] * 5 for _ in range(5)]

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_middle, request_late, request_early],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    sorted_order = sort_by_earliest_desired_pickup_time(darp_instance=darp_instance)

    assert sorted_order == [request_early.id, request_middle.id, request_late.id]


def test_best_insertion_for_request_returns_none_if_request_cannot_be_inserted():
    """
    Testet, ob `best_insertion_for_request` bei unmöglicher Insertion `None` zurückgibt
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    # Fahrt zum Pickup dauert 20 Minuten, Pickup-Buffer beträgt aber nur 5 Minuten.
    time_matrix = [
        [0, 1200, 0],
        [1200, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 10.0, 0.0],
        [10.0, 0.0, 5.0],
        [0.0, 5.0, 0.0],
    ]

    request = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=1,
        desired_pickup_time=start_time,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    routes = [Route(vehicle=vehicle, stops=[])]

    result = best_insertion_for_request(
        routes=routes,
        request_id=request.id,
        darp_instance=darp_instance
    )

    assert result is None


def test_best_insertion_for_request_returns_updated_route_for_feasible_request():
    """
    Testet, ob `best_insertion_for_request` eine Anfrage bei einer möglichen zulässigen Einfügeentscheidung eine Anfrage
    korrekt in die übergebenen Routen integriert.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    time_matrix = [[0] * 3 for _ in range(3)]
    distance_matrix = [[0.0] * 3 for _ in range(3)]

    request = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=1,
        desired_pickup_time=start_time,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    routes = [Route(vehicle=vehicle, stops=[])]

    result = best_insertion_for_request(
        routes=routes,
        request_id=request.id,
        darp_instance=darp_instance
    )

    assert result is not None

    route_index, best_route = result
    assert len(best_route.stops) == 2
    assert best_route.stops[0].kind == StopKind.PICKUP
    assert best_route.stops[1].kind == StopKind.DELIVERY
    assert best_route.stops[0].request_id == request.id
    assert best_route.stops[1].request_id == request.id


def test_greedy_construction_routes_accept_single_feasible_request():
    """
    Testet, ob `greedy_construction_routes` aus einer DarpInstance mit einer zulässigen Anfrage ein erwartbar korrektes
    DarpSolution-Objekt erstellt.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    time_matrix = [[0] * 3 for _ in range(3)]
    distance_matrix = [[0.0] * 3 for _ in range(3)]

    request = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=1,
        desired_pickup_time=start_time,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    solution = greedy_construction_routes(
        darp_instance=darp_instance
    )

    assert isinstance(solution, DarpSolution)
    assert len(solution.routes) == 1
    assert solution.served_requests == [request.id]
    assert solution.unserved_requests == []
    assert len(solution.routes[0].stops) == 2
    assert solution.routes[0].stops[0].kind == StopKind.PICKUP
    assert solution.routes[0].stops[1].kind == StopKind.DELIVERY


def test_greedy_construction_routes_accept_multiple_feasible_request():
    """
    Testet, ob `greedy_construction_routes` aus einer DarpInstance mit mehreren zulässigen Anfragen ein erwartbar
    korrektes DarpSolution-Objekt erstellt.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    time_matrix = [[0] * 180 for _ in range(3)]
    distance_matrix = [[0.0] * 180 for _ in range(3)]

    request_1 = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=1,
        desired_pickup_time=start_time,
    )

    request_2 = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=10),
    )

    request_3 = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=20),
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2, request_3],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    solution = greedy_construction_routes(
        darp_instance=darp_instance
    )

    assert isinstance(solution, DarpSolution)
    assert len(solution.routes) == 1
    assert solution.served_requests == [request_1.id, request_2.id, request_3.id]
    assert solution.unserved_requests == []
    assert len(solution.routes[0].stops) == 6
    assert solution.routes[0].stops[0].kind == StopKind.PICKUP
    assert solution.routes[0].stops[1].kind == StopKind.DELIVERY
    assert solution.routes[0].stops[2].kind == StopKind.PICKUP
    assert solution.routes[0].stops[3].kind == StopKind.DELIVERY
    assert solution.routes[0].stops[4].kind == StopKind.PICKUP
    assert solution.routes[0].stops[5].kind == StopKind.DELIVERY


def test_greedy_construction_routes_marks_unserved_request_at_no_feasible_insertion():
    """
    Testet, ob `greedy_construction_routes` aus einer DarpInstance mit nicht planbaren Anfragen ein erwartbar korrektes
    DarpSolution-Objekt erstellt.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    time_matrix = [
        [0, 1800, 0],
        [1800, 0, 600],
        [0, 600, 0],
    ]
    distance_matrix = [
        [0.0, 20.0, 0.0],
        [20.0, 0.0, 5.0],
        [0.0, 5.0, 0.0],
    ]

    request = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=1,
        desired_pickup_time=start_time,
    )
    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    solution = greedy_construction_routes(darp_instance=darp_instance)

    assert isinstance(solution, DarpSolution)
    assert len(solution.routes) == 1
    assert solution.served_requests == []
    assert solution.unserved_requests == [request.id]
    assert solution.routes[0].stops == []


def test_greedy_construction_routes_with_order_respects_request_order(monkeypatch):
    """
    Testet, ob `_greedy_construction_routes_with_order` die vorgegebene Reihenfolge der Anfragen einhält.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)
    pickup_3 = Location(lat=0.0, lon=0.0, matrix_node_id=5)
    delivery_3 = Location(lat=0.0, lon=0.0, matrix_node_id=6)

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=20),
    )

    request_2 = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=5),
    )

    request_3 = Request(
        pickup=pickup_3,
        delivery=delivery_3,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=5),
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    time_matrix = [[0] * 5 for _ in range(5)]
    distance_matrix = [[0.0] * 5 for _ in range(5)]

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2, request_3],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    observed_order: list[UUID] = []

    # Mock von `best_insertion_for_request`. Ziel ist nur die Reihenfolge der Abarbeitung zu speichern
    def mock_best_insertion_for_request(*, routes, request_id, darp_instance, use_early_exit = False):
        observed_order.append(request_id)

        request = darp_instance.requests[request_id]
        new_route = Route(
            vehicle=routes[0].vehicle,
            stops=[
                Stop(
                    kind=StopKind.PICKUP,
                    request_id=request_id,
                    location=request.pickup,
                ),
                Stop(
                    kind=StopKind.DELIVERY,
                    request_id=request_id,
                    location=request.delivery,
                ),
            ],
        )
        return 0, new_route

    monkeypatch.setattr(
        "darp_algorithms.core.greedy_heuristic.best_insertion_for_request",
        mock_best_insertion_for_request,
    )

    custom_order = [request_2.id, request_1.id, request_3.id]

    greedy_construction_routes_with_order(
        darp_instance=darp_instance,
        request_order=custom_order,
        use_early_exit=False,
    )

    assert observed_order == custom_order


def test_greedy_construction_routes_called_with_expected_params(monkeypatch):
    """
    Überprüft, ob `greedy_construction_routes` `greedy_construction_routes_with_order` mit den korrekten Parametern
    aufruft
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    time_matrix = [[0] * 5 for _ in range(3)]
    distance_matrix = [[0.0] * 5 for _ in range(3)]

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        passengers=1,
        desired_pickup_time=start_time,
    )

    request_2 = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=1,
        desired_pickup_time=start_time,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    request_order = [request_1.id, request_2.id]

    greedy_mock = Mock()
    monkeypatch.setattr(
        "darp_algorithms.core.greedy_heuristic.greedy_construction_routes_with_order",
        greedy_mock,
    )

    greedy_construction_routes(
        darp_instance=darp_instance,
    )

    greedy_mock.assert_called_once_with(
        darp_instance=darp_instance,
        request_order=request_order,
        use_early_exit=False,
    )


def test_greedy_construction_routes_time_restrictive_scenario_called_with_expected_params(monkeypatch):
    """
    Überprüft, ob `greedy_construction_routes` `greedy_construction_routes_with_order` mit den korrekten Parametern
    aufruft und eine Vorsortierung vornimmt.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    time_matrix = [[0] * 5 for _ in range(3)]
    distance_matrix = [[0.0] * 5 for _ in range(3)]

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        passengers=1,
        desired_pickup_time=start_time,
    )

    request_2 = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=1,
        desired_pickup_time=start_time,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
    )

    sorted_request_order = [request_1.id, request_2.id]

    sort_mock = Mock(return_value=sorted_request_order)
    greedy_mock = Mock()

    monkeypatch.setattr(
        "darp_algorithms.core.greedy_heuristic.sort_by_earliest_desired_pickup_time",
        sort_mock,
    )
    monkeypatch.setattr(
        "darp_algorithms.core.greedy_heuristic.greedy_construction_routes_with_order",
        greedy_mock,
    )

    greedy_construction_routes_time_restrictive_scenario(
        darp_instance=darp_instance,
    )

    sort_mock.assert_called_once_with(
        darp_instance=darp_instance,
    )
    greedy_mock.assert_called_once_with(
        darp_instance=darp_instance,
        request_order=sorted_request_order,
        use_early_exit=True,
    )
