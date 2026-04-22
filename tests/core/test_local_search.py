from datetime import datetime, timedelta

import pytest

from darp_algorithms.core import ConstraintConfig, DarpConfig, DarpInstance, DarpSolution, ObjectiveConfig
from darp_algorithms.core.local_search import exchange_requests, local_search_improvement, relocate_request
from darp_algorithms.core.solution_metrics import compute_solution_metrics
from darp_algorithms.domain import Location, Request, Stop, Vehicle
from darp_algorithms.domain.enums import StopKind
from darp_algorithms.domain.route import Route


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
        distance_matrix: list[list[float]]
) -> DarpInstance:
    darp_config = DarpConfig(
        vehicle_capacity=4,
        service_duration=timedelta(seconds=0),
        pickup_buffer=timedelta(minutes=10),
        objective_config=ObjectiveConfig(
            use_total_travel_time=True,
            travel_time_weight=1.0,
            use_travel_cost=True,
            travel_cost_weight=1.0,
            cost_per_kilometer=1.0,
        ),
        constraint_config=ConstraintConfig(
            use_max_ride_time=True,
            mrt_factor=2.0,
            fixed_max_ride_time=None,
        ),
    )

    return DarpInstance(
        darp_config=darp_config,
        vehicles=vehicles,
        requests={request.id: request for request in requests},
        request_order=[request.id for request in requests],
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )


def test_relocate_request_returns_expected_solution_structure():
    """
    Testet die Struktur der Lösung nach Anwendung des Relocate-Operators darp_algorithms.core.local_search.
    """
    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)
    pickup_req_3 = Location(lat=0.0, lon=0.0, matrix_node_id=5)
    delivery_req_3 = Location(lat=0.0, lon=0.0, matrix_node_id=6)

    request_1 = Request(
        pickup=pickup_req_1,
        delivery=delivery_req_1,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    request_2 = Request(
        pickup=pickup_req_2,
        delivery=delivery_req_2,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    request_3 = Request(
        pickup=pickup_req_3,
        delivery=delivery_req_3,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    time_matrix = [[0] * 7 for _ in range(7)]
    distance_matrix = [[0.0] * 7 for _ in range(7)]

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2, request_3],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix
    )

    served_requests = [request_1, request_2]
    stops = []
    for request in served_requests:
        stops.append(
            Stop(StopKind.PICKUP, request.id, request.pickup)
        )
        stops.append(
            Stop(StopKind.DELIVERY, request.id, request.delivery)
        )

    route = Route(
        vehicle=vehicle,
        stops=stops
    )

    darp_solution_before_relocate = DarpSolution(
        darp_instance=darp_instance,
        routes=[route],
        served_requests=[request_1.id, request_2.id],
        unserved_requests=[request_3.id],
    )

    darp_solution_after_relocate = relocate_request(
        darp_solution=darp_solution_before_relocate,
        request_id=request_1.id,
    )

    assert darp_solution_after_relocate is not None
    assert darp_solution_after_relocate.served_requests == darp_solution_before_relocate.served_requests
    assert darp_solution_after_relocate.unserved_requests == darp_solution_before_relocate.unserved_requests

    route_stops_after_relocate = darp_solution_after_relocate.routes[0].stops
    assert len(route_stops_after_relocate) == 4

    for served_request in served_requests:
        pickup_count = 0
        delivery_count = 0

        for stop in route_stops_after_relocate:
            if stop.request_id == served_request.id and stop.kind == StopKind.PICKUP:
                pickup_count += 1
            if stop.request_id == served_request.id and stop.kind == StopKind.DELIVERY:
                delivery_count += 1

        assert pickup_count == 1
        assert delivery_count == 1


def test_exchange_requests_returns_expected_solution_structure():
    """
    Testet die Struktur der Lösung nach erfolgreicher Anwendung des Exchange-Operators aus
    darp_algorithms.core.local_search.
    """
    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)
    pickup_req_3 = Location(lat=0.0, lon=0.0, matrix_node_id=5)
    delivery_req_3 = Location(lat=0.0, lon=0.0, matrix_node_id=6)

    request_1 = Request(
        pickup=pickup_req_1,
        delivery=delivery_req_1,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    request_2 = Request(
        pickup=pickup_req_2,
        delivery=delivery_req_2,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    request_3 = Request(
        pickup=pickup_req_3,
        delivery=delivery_req_3,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    time_matrix = [[0] * 7 for _ in range(7)]
    distance_matrix = [[0.0] * 7 for _ in range(7)]

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2, request_3],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix
    )

    served_requests = [request_1, request_2]
    stops = []
    for request in served_requests:
        stops.append(
            Stop(StopKind.PICKUP, request.id, request.pickup)
        )
        stops.append(
            Stop(StopKind.DELIVERY, request.id, request.delivery)
        )

    route = Route(
        vehicle=vehicle,
        stops=stops
    )

    darp_solution_before_exchange = DarpSolution(
        darp_instance=darp_instance,
        routes=[route],
        served_requests=[request_1.id, request_2.id],
        unserved_requests=[request_3.id],
    )

    darp_solution_after_exchange = exchange_requests(
        darp_solution=darp_solution_before_exchange,
        request_id_1=request_1.id,
        request_id_2=request_2.id
    )

    assert darp_solution_after_exchange is not None
    assert darp_solution_before_exchange.served_requests == darp_solution_after_exchange.served_requests
    assert darp_solution_before_exchange.unserved_requests == darp_solution_after_exchange.unserved_requests

    route_stops_after_exchange = darp_solution_after_exchange.routes[0].stops
    assert len(route_stops_after_exchange) == 4

    for served_request in served_requests:
        pickup_count = 0
        delivery_count = 0

        for stop in route_stops_after_exchange:
            if stop.request_id == served_request.id and stop.kind == StopKind.PICKUP:
                pickup_count += 1
            if stop.request_id == served_request.id and stop.kind == StopKind.DELIVERY:
                delivery_count += 1

        assert pickup_count == 1
        assert delivery_count == 1


def test_local_search_for_no_better_existing_solution():
    """
    Testet das Local-Search-Improvement Verfahren aus darp_algorithms.core.local_search.

    Es wird hierbei ein Szenario konstruiert, indem die Anfragen bereits optimal auf den Routen verteilt sind. Nachdem
    local_search_improvement() aufgerufen wird, sollten keine Änderungen in der Reihenfolge der Stopps innerhalb der
    Routen gemacht werden und der Zielfunktionswert der entstandenen Lösung erhalten bleibt.
    :return:
    """
    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    request_1 = Request(
        pickup=pickup_req_1,
        delivery=delivery_req_1,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    request_2 = Request(
        pickup=pickup_req_2,
        delivery=delivery_req_2,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    # Zeit- und Distanzmatritzen:
    # Hierbei sind die Abhol- und Zielknoten der jeweiligen Anfragen intern sehr nah beieinander. Eine abwechselnde
    # Abarbeitung der Anfragen würde in einem höheren Zielfunktionswert resultieren
    time_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 100, 400, 500],
        [0, 100, 0, 400, 500],
        [0, 400, 400, 0, 100],
        [0, 500, 500, 100, 0]
    ]

    distance_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 4, 5],
        [0, 1, 0, 4, 5],
        [0, 4, 4, 0, 1],
        [0, 5, 5, 1, 0]
    ]

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix
    )

    served_requests = [request_1, request_2]

    # Die Stopps befinden sich so bereits in der optimalen Reihenfolge, da die Abhol- und Zielknoten der jeweiligen
    # Anfragen in dieser Reihenfolge sehr nah beieinander liegen.
    stops = [
        Stop(StopKind.PICKUP, request_1.id, request_1.pickup),
        Stop(StopKind.DELIVERY, request_1.id, request_1.delivery),
        Stop(StopKind.PICKUP, request_2.id, request_2.pickup),
        Stop(StopKind.DELIVERY, request_2.id, request_2.delivery)
    ]

    darp_solution_before_local_search = DarpSolution(
        darp_instance=darp_instance,
        routes=[Route(vehicle=vehicle, stops=stops)],
        served_requests=[request_1.id, request_2.id],
        unserved_requests=[],
    )

    darp_solution_after_local_search = local_search_improvement(
        darp_solution=darp_solution_before_local_search
    )

    solution_metrics_before_local_search = compute_solution_metrics(darp_solution=darp_solution_before_local_search)
    solution_metrics_after_local_search = compute_solution_metrics(darp_solution=darp_solution_after_local_search)

    assert (
            solution_metrics_before_local_search.total_objective_value
            == pytest.approx(solution_metrics_after_local_search.total_objective_value)
    )

    assert darp_solution_before_local_search.served_requests == darp_solution_after_local_search.served_requests
    assert darp_solution_before_local_search.unserved_requests == darp_solution_after_local_search.unserved_requests

    route_stops_after_local_search_improvement = darp_solution_after_local_search.routes[0].stops
    assert len(route_stops_after_local_search_improvement) == 4

    for served_request in served_requests:
        pickup_count = 0
        delivery_count = 0

        for stop in route_stops_after_local_search_improvement:
            if stop.request_id == served_request.id and stop.kind == StopKind.PICKUP:
                pickup_count += 1
            if stop.request_id == served_request.id and stop.kind == StopKind.DELIVERY:
                delivery_count += 1

        assert pickup_count == 1
        assert delivery_count == 1


def test_local_search_for_better_existing_solution():
    """
    Testet das Local-Search-Improvement Verfahren aus darp_algorithms.core.local_search.

    Es wird hierbei ein Szenario konstruiert, indem die Anfragen schlecht auf den Routen verteilt sind. Nachdem
    local_search_improvement() aufgerufen wird, sollte Änderungen in der Reihenfolge der Stopps innerhalb der Routen
    gemacht werden, sodass der Zielfunktionswert der entstandenen Lösung sinkt.
    :return:
    """
    start_time = datetime(2026, 3, 5, 8, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_req_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_req_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    request_1 = Request(
        pickup=pickup_req_1,
        delivery=delivery_req_1,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    request_2 = Request(
        pickup=pickup_req_2,
        delivery=delivery_req_2,
        passengers=1,
        desired_pickup_time=start_time + timedelta(minutes=30),
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    # Zeit- und Distanzmatritzen
    time_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 100, 300, 500],
        [0, 100, 0, 500, 700],
        [0, 300, 500, 0, 100],
        [0, 500, 700, 100, 0]
    ]

    distance_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 3, 5],
        [0, 1, 0, 5, 7],
        [0, 3, 5, 0, 1],
        [0, 5, 7, 1, 0]
    ]

    darp_instance = create_instance(
        vehicles=[vehicle],
        requests=[request_1, request_2],
        time_matrix=time_matrix,
        distance_matrix=distance_matrix
    )

    served_requests = [request_1, request_2]

    # Die Stopps befinden sich so in der schlechten Ausgangsposition.
    # Die Reihenfolge Location 1 -> Location 3 -> Location 2 -> Location 4, sorgt für einen hohen Zielfunktionswert.
    # Ein geringer Zielfunktionswert ist bei Location 1 -> Location 2 -> Location 3 -> Location 4 zu erwarten, da in
    # dieser Reihenfolge die summierten Zeit- und Distanzwerte deutlich geringer sind.
    # Eine bessere Lösung entsteht durch ein einfaches Löschen und erneutes Einfügen der zweiten Anfragen
    # (Location 3 und 4). Dies sollte beispielsweise durch den Relocate-Operator möglich sein.
    stops = [
        Stop(StopKind.PICKUP, request_1.id, request_1.pickup),
        Stop(StopKind.PICKUP, request_2.id, request_2.pickup),
        Stop(StopKind.DELIVERY, request_1.id, request_1.delivery),
        Stop(StopKind.DELIVERY, request_2.id, request_2.delivery)
    ]

    darp_solution_before_local_search = DarpSolution(
        darp_instance=darp_instance,
        routes=[Route(vehicle=vehicle, stops=stops)],
        served_requests=[request_1.id, request_2.id],
        unserved_requests=[],
    )

    darp_solution_after_local_search = local_search_improvement(
        darp_solution=darp_solution_before_local_search
    )

    solution_metrics_before_local_search = compute_solution_metrics(darp_solution=darp_solution_before_local_search)
    solution_metrics_after_local_search = compute_solution_metrics(darp_solution=darp_solution_after_local_search)

    assert (
            solution_metrics_before_local_search.total_objective_value
            > solution_metrics_after_local_search.total_objective_value
    )

    assert darp_solution_before_local_search.served_requests == darp_solution_after_local_search.served_requests
    assert darp_solution_before_local_search.unserved_requests == darp_solution_after_local_search.unserved_requests

    route_stops_after_local_search_improvement = darp_solution_after_local_search.routes[0].stops
    assert len(route_stops_after_local_search_improvement) == 4

    for served_request in served_requests:
        pickup_count = 0
        delivery_count = 0

        for stop in route_stops_after_local_search_improvement:
            if stop.request_id == served_request.id and stop.kind == StopKind.PICKUP:
                pickup_count += 1
            if stop.request_id == served_request.id and stop.kind == StopKind.DELIVERY:
                delivery_count += 1

        assert pickup_count == 1
        assert delivery_count == 1
