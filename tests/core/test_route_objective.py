from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from darp_algorithms.core.constraint_config import ConstraintConfig
from darp_algorithms.core.darp_config import DarpConfig
from darp_algorithms.core.objective_config import ObjectiveConfig
from darp_algorithms.core.route_objective import compute_solution_objective_function
from darp_algorithms.core.route_state import RouteState
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


def build_modifiable_route_state(
        *,
        darp_config,
        time_matrix,
        distance_matrix,
        start_time,
        depot,
        pickup,
        delivery,
        passengers
) -> RouteState:
    request = Request(
        pickup=pickup,
        delivery=delivery,
        passengers=passengers,
        desired_pickup_time=start_time,
    )

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time,
    )

    route = Route(
        vehicle=vehicle,
        stops=[
            Stop(StopKind.PICKUP, request.id, pickup),
            Stop(StopKind.DELIVERY, request.id, delivery),
        ],
    )

    state = RouteState(
        darp_config=darp_config,
        route=route,
        requests={request.id: request},
        travel_time=travel_time_fn(time_matrix),
        travel_distance=travel_distance_fn(distance_matrix),
    )
    state.recompute()
    return state


def build_standard_route_state(
        *,
        objective_config: ObjectiveConfig,
        service_duration: timedelta = timedelta(seconds=0),
) -> RouteState:
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

    darp_config = DarpConfig(
        vehicle_capacity=4,
        service_duration=service_duration,
        objective_config=objective_config,
        constraint_config=ConstraintConfig(),
    )

    route_state = build_modifiable_route_state(
        darp_config=darp_config,
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        start_time=start_time,
        depot=depot,
        pickup=pickup,
        delivery=delivery,
        passengers=1
    )

    route_state.recompute()
    return route_state


def test_compute_solution_objective_function_only_travel_time():
    """
    Testet, ob `compute_solution_objective_function` bei der Berechnung des Zielfunktionswerts nur die Gesamt-Fahrtzeit
    berücksichtigt, wenn die restlichen Optimierungsziele deaktiviert sind.
    """
    objective_config = ObjectiveConfig(
        use_total_travel_time=True,
        travel_time_weight=1.0,
        use_travel_cost=False,
    )

    route_state = build_standard_route_state(objective_config=objective_config)
    objective_value = compute_solution_objective_function(
        route_states=[route_state],
        objective_config=objective_config
    )

    assert objective_value == 600.0


def test_compute_solution_objective_function_only_travel_cost():
    """
    Testet, ob `compute_solution_objective_function` bei der Berechnung des Zielfunktionswerts nur die
    Gesamt-Fahrtkosten berücksichtigt, wenn die restlichen Optimierungsziele deaktiviert sind.
    """
    objective_config = ObjectiveConfig(
        use_total_travel_time=False,
        use_travel_cost=True,
        travel_cost_weight=1.0,
        cost_per_kilometer=2.0,
    )

    route_state = build_standard_route_state(objective_config=objective_config)
    objective_value = compute_solution_objective_function(
        route_states=[route_state],
        objective_config=objective_config
    )

    assert objective_value == 10.0


def test_compute_solution_objective_function_only_imbalance():
    """
    Testet, ob `compute_solution_objective_function` bei der Berechnung des Zielfunktionswerts nur die Imbalance
    berücksichtigt, wenn die restlichen Optimierungsziele deaktiviert sind.
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    time_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 600, 0, 0],
        [0, 600, 0, 0, 0],
        [0, 0, 0, 0, 600],
        [0, 0, 0, 600, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 5.0, 0.0, 0.0],
        [0.0, 5.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 5.0],
        [0.0, 0.0, 0.0, 5.0, 0.0],
    ]

    objective_config = ObjectiveConfig(
        use_total_travel_time=False,
        use_travel_cost=False,
        use_capacity_balancing=True,
        capacity_balancing_weight=1.0,
    )

    darp_config = DarpConfig(
        vehicle_capacity=4,
        objective_config=objective_config,
        constraint_config=ConstraintConfig(),
    )

    route_state_1 = build_modifiable_route_state(
        darp_config=darp_config,
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        start_time=start_time,
        depot=depot,
        pickup=pickup_1,
        delivery=delivery_1,
        passengers=2,
    )
    route_state_2 = build_modifiable_route_state(
        darp_config=darp_config,
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        start_time=start_time,
        depot=depot,
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=4,
    )

    objective_value = compute_solution_objective_function(
        route_states=[route_state_1, route_state_2],
        objective_config=objective_config,
    )

    assert objective_value == 0.25


def test_compute_solution_objective_function_combined():
    """
    Testet, ob `compute_solution_objective_function` alle Optimierungsziele korrekt bei der Berechnung des
    Zielfunktionswerts berücksichtigt
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    time_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 10, 0, 0],
        [0, 10, 0, 0, 0],
        [0, 0, 0, 0, 10],
        [0, 0, 0, 10, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 5.0, 0.0, 0.0],
        [0.0, 5.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 5.0],
        [0.0, 0.0, 0.0, 5.0, 0.0],
    ]

    objective_config = ObjectiveConfig(
        use_total_travel_time=True,
        travel_time_weight=1.0,
        use_travel_cost=True,
        travel_cost_weight=1,
        cost_per_kilometer=2.0,
        use_capacity_balancing=True,
        capacity_balancing_weight=1.0,
    )

    darp_config = DarpConfig(
        vehicle_capacity=4,
        objective_config=objective_config,
        constraint_config=ConstraintConfig(),
    )

    route_state_1 = build_modifiable_route_state(
        darp_config=darp_config,
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        start_time=start_time,
        depot=depot,
        pickup=pickup_1,
        delivery=delivery_1,
        passengers=2,
    )
    route_state_2 = build_modifiable_route_state(
        darp_config=darp_config,
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        start_time=start_time,
        depot=depot,
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=4,
    )

    objective_value = compute_solution_objective_function(
        route_states=[route_state_1, route_state_2],
        objective_config=objective_config,
    )

    # 20 (travel_time) + 20 (travel_cost) + 0.25 (imbalance)
    assert objective_value == 40.25


def test_compute_solution_objective_function_respects_weights():
    """
    Testet, ob `compute_solution_objective_function` die Gewichtungsfaktoren der Zielfunktion korrekt berücksichtigt
    """
    start_time = datetime(2026, 3, 5, 10, 0, 0)
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0)
    pickup_1 = Location(lat=0.0, lon=0.0, matrix_node_id=1)
    delivery_1 = Location(lat=0.0, lon=0.0, matrix_node_id=2)
    pickup_2 = Location(lat=0.0, lon=0.0, matrix_node_id=3)
    delivery_2 = Location(lat=0.0, lon=0.0, matrix_node_id=4)

    time_matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 10, 0, 0],
        [0, 10, 0, 0, 0],
        [0, 0, 0, 0, 10],
        [0, 0, 0, 10, 0],
    ]
    distance_matrix = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 5.0, 0.0, 0.0],
        [0.0, 5.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 5.0],
        [0.0, 0.0, 0.0, 5.0, 0.0],
    ]

    objective_config = ObjectiveConfig(
        use_total_travel_time=True,
        travel_time_weight=2.0,
        use_travel_cost=True,
        travel_cost_weight=4,
        cost_per_kilometer=2.0,
        use_capacity_balancing=True,
        capacity_balancing_weight=8.0,
    )

    darp_config = DarpConfig(
        vehicle_capacity=4,
        objective_config=objective_config,
        constraint_config=ConstraintConfig(),
    )

    route_state_1 = build_modifiable_route_state(
        darp_config=darp_config,
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        start_time=start_time,
        depot=depot,
        pickup=pickup_1,
        delivery=delivery_1,
        passengers=2,
    )
    route_state_2 = build_modifiable_route_state(
        darp_config=darp_config,
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        start_time=start_time,
        depot=depot,
        pickup=pickup_2,
        delivery=delivery_2,
        passengers=4,
    )

    objective_value = compute_solution_objective_function(
        route_states=[route_state_1, route_state_2],
        objective_config=objective_config,
    )

    # 2 * 20 (travel_time) + 4 * 20 (travel_cost) + 8 * 0.25 (imbalance)
    assert objective_value == 122


def test_compute_solution_objective_function_all_components_disabled():
    """
    Testet, ob `compute_solution_objective_function` einen Zielfunktionswert von 0 zurückgibt, sofern keine
    Optimierungsziele aktiviert sind.
    """
    objective_config = ObjectiveConfig(
        use_total_travel_time=False,
        use_travel_cost=False,
        use_capacity_balancing=False,
    )

    route_state = build_standard_route_state(objective_config=objective_config)
    objective_value = compute_solution_objective_function(
        route_states=[route_state],
        objective_config=objective_config,
    )

    assert objective_value == 0.0


def test_compute_solution_objective_function_empty_route():
    """
    Testet, ob `compute_solution_objective_function` einen Zielfunktionswert von 0 zurückgibt, sofern nur eine leere
    Route übergeben wird.
    """
    depot = Location(lat=0.0, lon=0.0, matrix_node_id=0, id=uuid4())
    start_time = datetime(2026, 3, 5, 10, 0, 0)

    vehicle = Vehicle(
        start_position=depot,
        start_time=start_time
    )

    route = Route(vehicle=vehicle, stops=[])

    objective_config = ObjectiveConfig(
        use_total_travel_time=True,
        use_travel_cost=True,
        use_capacity_balancing=True
    )
    darp_config = DarpConfig(
        vehicle_capacity=4,
        objective_config=objective_config,
        constraint_config=ConstraintConfig(),
    )

    route_state = RouteState(
        darp_config=darp_config,
        route=route,
        requests={},
        travel_time=travel_time_fn([[0]]),
        travel_distance=travel_distance_fn([[0.0]]),
        early_exit_on_violation=False,
    )
    route_state.recompute()

    objective_value = compute_solution_objective_function(
        route_states=[route_state],
        objective_config=objective_config,
    )

    assert objective_value == 0.0
