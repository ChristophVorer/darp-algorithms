from __future__ import annotations

from datetime import datetime, timedelta

from darp_algorithms.core import ConstraintConfig, DarpConfig, RouteState
from darp_algorithms.domain import Request, Vehicle
from darp_algorithms.domain.enums.stop_kind import StopKind
from darp_algorithms.domain.enums.violation_type import ViolationType
from darp_algorithms.domain.location import Location
from darp_algorithms.domain.route import Route
from darp_algorithms.domain.stop import Stop


def travel_time_fn(matrix_seconds):
    def travel_time(a: Location, b: Location) -> timedelta:
        return timedelta(seconds=matrix_seconds[a.matrix_node_id][b.matrix_node_id])

    return travel_time


def travel_distance_fn(matrix_distances):
    def travel_distance(a: Location, b: Location) -> float:
        return matrix_distances[a.matrix_node_id][b.matrix_node_id]

    return travel_distance


def test_route_state_recompute_computes_route_metrics():
    """
    Testet, ob die `recompute` Funktion aus `RouteState` die Routenmetriken für die Fahrzeugauslastung sowie der
    Gesamt-Fahrtzeit und den Gesamt-Fahrtkosten korrekt berechnet.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)

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

    request = Request(
        pickup=pickup,
        delivery=delivery,
        desired_pickup_time=start_time,
        passengers=2,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    route = Route(
        vehicle=vehicle,
        stops=[
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.DELIVERY, request.id, delivery),
        ],
    )

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is True
    assert route_state.violations == []

    assert route_state.arrival == [
        start_time,
        start_time + timedelta(minutes=10),
    ]
    assert route_state.start_service == [
        start_time,
        start_time + timedelta(minutes=10),
    ]
    assert route_state.departure == [
        start_time,
        start_time + timedelta(minutes=10),
    ]
    assert route_state.load == [2, 0]

    assert route_state.total_travel_time == timedelta(minutes=10)
    assert route_state.total_travel_distance == 5.0


def test_route_state_respects_service_duration():
    """
    Testet, ob `recompute` Funktion aus `RouteState` die Service-Zeit an den Knoten berücksichtigt.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
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
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.DELIVERY, request.id, delivery),
        ],
    )

    time_matrix = [
        [0, 0, 0],
        [0, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0],
        [0.0, 2.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            service_duration=timedelta(minutes=2)
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.arrival[0] == start_time
    assert route_state.start_service[0] == start_time
    assert route_state.departure[0] == start_time + timedelta(minutes=2)

    assert route_state.arrival[1] == start_time + timedelta(minutes=7)
    assert route_state.start_service[1] == start_time + timedelta(minutes=7)
    assert route_state.departure[1] == start_time + timedelta(minutes=9)


def test_route_state_detects_time_window_violation():
    """
    Testet, ob `recompute` Funktion aus `RouteState` eine Zeitfenster-Verletzung bei einer zu späten Abholung erkennt
    und eine entsprechende Violation wirft.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
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
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.DELIVERY, request.id, delivery),
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

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            pickup_buffer=timedelta(minutes=10)
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert len(route_state.violations) == 1
    assert route_state.violations[0].type == ViolationType.TIME_WINDOW


def test_route_state_detects_precedence_violation():
    """
    Testet, ob `recompute` Funktion aus `RouteState` eine Zeitfenster-Verletzung bei einer zu späten Abholung erkennt
    und eine entsprechende Violation festhält.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
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
            Stop(StopKind.DELIVERY, request.id, delivery),
            Stop(StopKind.PICKUP, request.id, pickup),
        ],
    )

    time_matrix = [
        [0, 0, 0],
        [0, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0],
        [0.0, 2.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            )
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert any(v.type == ViolationType.PRECEDENCE for v in route_state.violations)


def test_route_state_detects_double_pickup_violation():
    """
    Testet, ob `recompute` Funktion aus `RouteState` eine Dopplung eines Abholknotens abfängt und eine entsprechende
    Violation festhält.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
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
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.DELIVERY, request.id, delivery),
        ],
    )

    time_matrix = [
        [0, 0, 0],
        [0, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0],
        [0.0, 2.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            )
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert any(v.type == ViolationType.DOUBLED_PICKUP for v in route_state.violations)


def test_route_state_detects_capacity_violation():
    """
    Testet, ob `recompute` Funktion aus `RouteState` eine Kapazitätsverletzung erkennt und eine entsprechende Violation
    festhält.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
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

    route = Route(
        vehicle=vehicle,
        stops=[
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.DELIVERY, request.id, delivery),
        ],
    )

    time_matrix = [
        [0, 0, 0],
        [0, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0],
        [0.0, 2.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=2,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            )
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert any(v.type == ViolationType.CAPACITY for v in route_state.violations)


def test_route_state_detects_negative_load_as_capacity_violation():
    """
    Testet, ob `recompute` Funktion aus `RouteState` eine negative Kapazität als Fehler erkennt und eine entsprechende
    Kapazitäts-Violation festhält.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
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
        stops=[Stop(StopKind.DELIVERY, request.id, delivery)],
    )

    time_matrix = [
        [0, 0, 0],
        [0, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0],
        [0.0, 2.0, 0.0],
    ]
    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            )
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert any(v.type == ViolationType.CAPACITY for v in route_state.violations)


def test_route_state_detects_max_ride_time_violation_with_fixed_limit():
    """
    Testet, ob `recompute` Funktion aus `RouteState` eine Verletzung der maximalen Fahrtzeit angegeben über den Wert
    `fixed_max_ride_time` als Fehler erkennt und eine entsprechende Violation festhält.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    wait = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=3)

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
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.PICKUP, request.id, wait),
            Stop(StopKind.DELIVERY, request.id, delivery),
        ],
    )

    time_matrix = [
        [0, 0, 0, 0],
        [0, 0, 600, 900],
        [0, 600, 0, 900],
        [0, 900, 900, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 3.0, 6.0],
        [0.0, 3.0, 0.0, 6.0],
        [0.0, 6.0, 6.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            constraint_config=ConstraintConfig(
                use_max_ride_time=True,
                mrt_factor=None,
                fixed_max_ride_time=timedelta(minutes=10),
            ),
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert any(v.type == ViolationType.MAX_RIDE_TIME for v in route_state.violations)


def test_route_state_uses_mrt_factor_if_no_fixed_max_ride_time_is_given():
    """
    Testet, ob `recompute` Funktion aus `RouteState` eine Verletzung der maximalen Fahrtzeit angegeben über den Wert
    `mrt_factor` als Fehler erkennt und eine entsprechende Violation festhält.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=3)

    request_1 = Request(
        pickup=pickup_1,
        delivery=delivery_1,
        desired_pickup_time=start_time,
        passengers=1,
    )
    request_2 = Request(
        pickup=pickup_2,
        delivery=pickup_2,
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
            Stop(StopKind.PICKUP, request_1.id, pickup_1),
            Stop(StopKind.PICKUP, request_2.id, pickup_2),
            Stop(StopKind.DELIVERY, request_1.id, delivery_1),
        ],
    )

    time_matrix = [
        [0, 0, 0, 0],
        [0, 0, 600, 900],
        [0, 600, 0, 900],
        [0, 900, 900, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 3.0, 6.0],
        [0.0, 3.0, 0.0, 6.0],
        [0.0, 6.0, 6.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            constraint_config=ConstraintConfig(
                use_max_ride_time=True,
                mrt_factor=2,
                fixed_max_ride_time=timedelta(minutes=10),
            ),
        ),
        route=route,
        requests={request_1.id: request_1, request_2.id: request_2},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert any(v.type == ViolationType.MAX_RIDE_TIME for v in route_state.violations)


def test_route_state_recompute_resets_previous_state():
    """
    Testet, ob `recompute` Funktion aus `RouteState` die Routenmetriken jedes Mal resettet und für die aktuelle Belegung
     neu berechnet.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
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
        stops=[Stop(StopKind.PICKUP, request.id, pickup)],
    )

    time_matrix = [
        [0, 0, 0],
        [0, 0, 300],
        [0, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0],
        [0.0, 2.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            ),
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    route_state.recompute()

    assert len(route_state.arrival) == 1
    assert len(route_state.load) == 1

    route.stops.append(Stop(StopKind.DELIVERY, request.id, delivery))
    route_state.recompute()

    assert len(route_state.arrival) == 2
    assert len(route_state.start_service) == 2
    assert len(route_state.departure) == 2
    assert len(route_state.load) == 2
    assert route_state.load == [1, 0]


def test_route_state_early_exit_on_violation():
    """
    Testet, ob `recompute` Funktion aus `RouteState`, sofern `early_exit_on_violation` gesetzt ist, bei der ersten
    Verletzung einer Nebenbedingung die weitere Berechnung der Routenmetriken beendet.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    extra = Location(lat=0.0, lon=0.0, matrix_node_id=3)

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

    # Diese Route-Konfiguration verursacht eine Präzedenz-Verletzung
    route = Route(
        vehicle=vehicle,
        stops=[
            Stop(StopKind.DELIVERY, request.id, delivery),
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.DELIVERY, request.id, extra),
        ],
    )

    time_matrix = [
        [0, 0, 0, 0],
        [0, 0, 300, 300],
        [0, 300, 0, 300],
        [0, 300, 300, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0, 2.0],
        [0.0, 2.0, 0.0, 2.0],
        [0.0, 2.0, 2.0, 0.0],
    ]

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=4,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            ),
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
        early_exit_on_violation=True,
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert len(route_state.violations) == 1
    assert route_state.violations[0].type == ViolationType.PRECEDENCE

    assert len(route_state.arrival) == 0
    assert len(route_state.start_service) == 0
    assert len(route_state.departure) == 0
    assert len(route_state.load) == 0


def test_route_state_without_early_exit_collects_multiple_violations():
    """
    Testet, ob `recompute` Funktion aus `RouteState`, sofern `early_exit_on_violation` nicht gesetzt ist, alle
    vorhandenen Verletzungen von Nebenbedingungen sammelt und die weitere Berechnung der Routenmetriken nicht beendet.
    """

    start_time = datetime(2026, 3, 5, 10, 0, 0)
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

    # Diese Route-Konfiguration verursacht eine Präzedenz-Verletzung
    route = Route(
        vehicle=vehicle,
        stops=[
            Stop(StopKind.DELIVERY, request.id, delivery),
            Stop(StopKind.PICKUP, request.id, pickup),
        ],
    )

    # Diese Zeitmatrix verursacht eine Zeitfenster-Verletzung
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

    route_state = RouteState(
        darp_config=DarpConfig(
            vehicle_capacity=2,
            constraint_config=ConstraintConfig(
                use_max_ride_time=False,
            ),
        ),
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
        early_exit_on_violation=False,
    )
    route_state.recompute()

    assert route_state.is_feasible() is False
    assert len(route_state.violations) >= 2
    assert any(v.type == ViolationType.PRECEDENCE for v in route_state.violations)
    assert any(v.type == ViolationType.CAPACITY for v in route_state.violations)
