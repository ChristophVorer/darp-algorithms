from __future__ import annotations

from datetime import datetime, timedelta

from darp_algorithms.core.constraint_config import ConstraintConfig
from darp_algorithms.core.darp_config import DarpConfig
from darp_algorithms.core.darp_instance import DarpInstance
from darp_algorithms.core.darp_solution import DarpSolution
from darp_algorithms.core.objective_config import ObjectiveConfig
from darp_algorithms.core.solution_metrics import compute_solution_metrics
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


def test_compute_solution_metrics_for_empty_solution():
    """
    Testet, ob `compute_solution_metrics` korrekte Lösungsmetriken für eine "leere" Lösung berechnet
    """
    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    darp_instance = DarpInstance(
        darp_config=DarpConfig(
            vehicle_capacity=4,
        ),
        vehicles=[vehicle],
        requests={},
        request_order=[],
        travel_time=travel_time_fn(0),
        travel_distance=travel_distance_fn(0.0),
    )

    solution = DarpSolution(
        darp_instance=darp_instance,
        routes=[Route(vehicle=vehicle, stops=[])],
        served_requests=[],
        unserved_requests=[],
    )

    metrics = compute_solution_metrics(darp_solution=solution)

    assert metrics.number_of_routes == 1
    assert metrics.number_of_requests_total == 0
    assert metrics.number_of_requests_served == 0
    assert metrics.number_of_requests_unserved == 0
    assert metrics.percentage_of_served_requests == 0.0

    assert metrics.total_travel_time == 0.0
    assert metrics.total_travel_distance == 0.0
    assert metrics.total_objective_value == 0.0

    assert metrics.number_of_feasible_routes == 1
    assert metrics.number_of_infeasible_routes == 0
    assert metrics.number_of_total_violations == 0


def test_compute_solution_metrics_for_fully_served_feasible_solution():
    """
    Testet, ob `compute_solution_metrics` korrekte Lösungsmetriken für eine zulässige Lösung bestehend ausschließlich
    bedienten Anfrage(n) berechnet.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

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

    route = Route(
        vehicle=vehicle,
        stops=[
            Stop(kind=StopKind.PICKUP, request_id=request.id, location=pickup),
            Stop(kind=StopKind.DELIVERY, request_id=request.id, location=delivery),
        ],
    )

    time_matrix = [
        [0, 0, 0],
        [0, 0, 600],
        [0, 600, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 5.0],
        [0.0, 5.0, 0.0],
    ]

    darp_instance = DarpInstance(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            objective_config=ObjectiveConfig(
                use_total_travel_time=True,
                travel_time_weight=1.0,
                use_travel_cost=True,
                travel_cost_weight=1.0,
                cost_per_kilometer=2.0,
            )
        ),
        vehicles=[vehicle],
        requests={request.id: request},
        request_order=[request.id],
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )

    solution = DarpSolution(
        darp_instance=darp_instance,
        routes=[route],
        served_requests=[request.id],
        unserved_requests=[],
    )

    metrics = compute_solution_metrics(darp_solution=solution)

    assert metrics.number_of_routes == 1
    assert metrics.number_of_requests_total == 1
    assert metrics.number_of_requests_served == 1
    assert metrics.number_of_requests_unserved == 0
    assert metrics.percentage_of_served_requests == 100.0

    assert metrics.total_travel_time == 600.0
    assert metrics.total_travel_distance == 5.0
    assert metrics.total_objective_value == 610.0

    assert metrics.number_of_feasible_routes == 1
    assert metrics.number_of_infeasible_routes == 0
    assert metrics.number_of_total_violations == 0


def test_compute_solution_metrics_computes_unserved_requests():
    """
    Testet, ob `compute_solution_metrics` den Anteil nicht bedienter Anfragen korrekt berechnet.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        desired_pickup_time=start_time,
        passengers=1
    )

    request_2 = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        desired_pickup_time=start_time + timedelta(minutes=5),
        passengers=1
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    route = Route(
        vehicle=vehicle,
        stops=[
            Stop(kind=StopKind.PICKUP, request_id=request_1.id, location=pickup_1),
            Stop(kind=StopKind.DELIVERY, request_id=request_1.id, location=delivery_1),
        ],
    )

    time_matrix = [[0] * 5 for _ in range(5)]
    distance_matrix = [[0.0] * 5 for _ in range(5)]

    darp_instance = DarpInstance(
        darp_config=DarpConfig(
            vehicle_capacity=4
        ),
        vehicles=[vehicle],
        requests={request_1.id: request_1, request_2.id: request_2},
        request_order=[request_1.id, request_2.id],
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )

    solution = DarpSolution(
        darp_instance=darp_instance,
        routes=[route],
        served_requests=[request_1.id],
        unserved_requests=[request_2.id],
    )

    metrics = compute_solution_metrics(darp_solution=solution)

    assert metrics.number_of_requests_total == 2
    assert metrics.number_of_requests_served == 1
    assert metrics.number_of_requests_unserved == 1
    assert metrics.percentage_of_served_requests == 50.0


def test_compute_solution_metrics_multiple_feasible_routes():
    """
    Testet, ob `compute_solution_metrics` die Lösungsmetriken für mehrere zulässige Routen korrekt berechnet.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        desired_pickup_time=start_time,
        passengers=1,
    )
    request_2 = Request(
        pickup=pickup_2,
        delivery=delivery_2,
        desired_pickup_time=start_time,
        passengers=1
    )

    vehicle_1 = Vehicle(
        start_position=depot,
        start_time=start_time
    )
    vehicle_2 = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    route_1 = Route(
        vehicle=vehicle_1,
        stops=[
            Stop(kind=StopKind.PICKUP, request_id=request_1.id, location=pickup_1),
            Stop(kind=StopKind.DELIVERY, request_id=request_1.id, location=delivery_1),
        ],
    )
    route_2 = Route(
        vehicle=vehicle_2,
        stops=[
            Stop(kind=StopKind.PICKUP, request_id=request_2.id, location=pickup_2),
            Stop(kind=StopKind.DELIVERY, request_id=request_2.id, location=delivery_2),
        ],
    )

    time_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 600, 0, 0],
        [0, 600, 0, 0, 0],
        [0, 0, 0, 0, 300],
        [0, 0, 0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 5.0, 0.0, 0.0],
        [0.0, 5.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 2.0],
        [0.0, 0.0, 0.0, 2.0, 0.0],
    ]

    darp_instance = DarpInstance(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            objective_config=ObjectiveConfig(
                use_total_travel_time=True,
                travel_time_weight=1.0,
                use_travel_cost=True,
                travel_cost_weight=1.0,
                cost_per_kilometer=2.0,
            )
        ),
        vehicles=[vehicle_1, vehicle_2],
        requests={request_1.id: request_1, request_2.id: request_2},
        request_order=[request_1.id, request_2.id],
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )

    solution = DarpSolution(
        darp_instance=darp_instance,
        routes=[route_1, route_2],
        served_requests=[request_1.id, request_2.id],
        unserved_requests=[],
    )

    metrics = compute_solution_metrics(darp_solution=solution)

    assert metrics.number_of_routes == 2
    assert metrics.number_of_requests_total == 2
    assert metrics.number_of_requests_served == 2
    assert metrics.number_of_requests_unserved == 0
    assert metrics.percentage_of_served_requests == 100.0

    assert metrics.total_travel_time == 900.0
    assert metrics.total_travel_distance == 7.0
    assert metrics.total_objective_value == 914.0

    assert metrics.number_of_feasible_routes == 2
    assert metrics.number_of_infeasible_routes == 0
    assert metrics.number_of_total_violations == 0


def test_compute_solution_metrics_computes_infeasible_routes_and_violations():
    """
    Testet, ob `compute_solution_metrics` unzulässige Routen und Nebenbedingungsverletzung korrekt erkennt und in den
    Lösungsmetriken ausgibt.
    """

    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

    request = Request(
        pickup=pickup,
        delivery=delivery,
        desired_pickup_time=start_time,
        passengers=3,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    infeasible_route = Route(
        vehicle=vehicle,
        stops=[
            Stop(kind=StopKind.DELIVERY, request_id=request.id, location=delivery),
            Stop(kind=StopKind.PICKUP, request_id=request.id, location=pickup),
        ],
    )

    time_matrix = [
        [0, 900, 0],
        [900, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 8.0, 0.0],
        [8.0, 0.0, 2.0],
        [0.0, 2.0, 0.0],
    ]

    darp_instance = DarpInstance(
        darp_config=DarpConfig(
            vehicle_capacity=2,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            )
        ),
        vehicles=[vehicle],
        requests={request.id: request},
        request_order=[request.id],
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )

    solution = DarpSolution(
        darp_instance=darp_instance,
        routes=[infeasible_route],
        served_requests=[],
        unserved_requests=[request.id],
    )

    metrics = compute_solution_metrics(darp_solution=solution)

    assert metrics.number_of_routes == 1
    assert metrics.number_of_requests_total == 1
    assert metrics.number_of_requests_served == 0
    assert metrics.number_of_requests_unserved == 1
    assert metrics.percentage_of_served_requests == 0.0

    assert metrics.number_of_feasible_routes == 0
    assert metrics.number_of_infeasible_routes == 1
    assert metrics.number_of_total_violations >= 2
