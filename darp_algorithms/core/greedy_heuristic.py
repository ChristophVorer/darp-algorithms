from __future__ import annotations

from typing import Optional
from uuid import UUID

from darp_algorithms.domain.enums.stop_kind import StopKind
from darp_algorithms.domain.route import Route
from darp_algorithms.domain.stop import Stop

from .darp_instance import DarpInstance
from .darp_solution import DarpSolution
from .route_objective import compute_route_objective_function
from .route_state import RouteState


def best_insertion_for_request(
        *,
        routes: list[Route],
        request_id: UUID,
        darp_instance: DarpInstance,
        use_early_exit: bool = False,
) -> Optional[tuple[int, Route]]:
    """
    Sequenzielle 2-Phasen-Greedy-Heuristik zur Einfügung einer einzelnen Anfrage.

    1. Phase:
    Beste zulässige Einfügeposition des Pickup-Stopps über alle Routen bestimmen.

    2. Phase:
    Beste zulässige Einfügeposition des Delivery-Stopps innerhalb der zuvor
    gewählten Route bestimmen.

    Returns:
        Optional[tuple[int, Route]]:
            Tupel aus Routenindex und aktualisierter Route.
            Gibt None zurück, wenn keine zulässige Einfügung existiert.
    """
    req = darp_instance.requests[request_id]

    pickup_stop = Stop(
        kind=StopKind.PICKUP,
        request_id=request_id,
        location=req.pickup,
        planned_time=None,
    )
    delivery_stop = Stop(
        kind=StopKind.DELIVERY,
        request_id=request_id,
        location=req.delivery,
        planned_time=None,
    )

    best_pickup_route: Optional[Route] = None
    best_pickup_position = -1
    best_pickup_delta = float("inf")
    best_route_index = -1
    best_pickup_route_objective_value = 0.0

    best_whole_route: Optional[Route] = None
    best_whole_delta = float("inf")

    for route_index, route in enumerate(routes):
        route_state = RouteState(
            darp_config=darp_instance.darp_config,
            route=route,
            requests=darp_instance.requests,
            travel_time=darp_instance.travel_time,
            travel_distance=darp_instance.travel_distance,
            early_exit_on_violation=use_early_exit,
        )
        route_state.recompute()
        route_objective_value = compute_route_objective_function(route_state)

        route_length = len(route.stops)
        for i in range(route_length + 1):
            pickup_route = Route(
                vehicle=route.vehicle,
                stops=list(route.stops),
            )
            pickup_route.stops.insert(i, pickup_stop)

            pickup_state = RouteState(
                darp_config=darp_instance.darp_config,
                route=pickup_route,
                requests=darp_instance.requests,
                travel_time=darp_instance.travel_time,
                travel_distance=darp_instance.travel_distance,
                early_exit_on_violation=use_early_exit,
            )
            pickup_state.recompute()

            if not pickup_state.is_feasible():
                continue

            pickup_objective_value = compute_route_objective_function(pickup_state)
            pickup_delta = pickup_objective_value - route_objective_value

            if pickup_delta < best_pickup_delta:
                best_pickup_delta = pickup_delta
                best_pickup_position = i
                best_pickup_route = pickup_route
                best_pickup_route_objective_value = pickup_objective_value
                best_route_index = route_index

    if best_pickup_route is None:
        return None

    route_with_pickup = best_pickup_route

    route_length = len(route_with_pickup.stops)
    for j in range(best_pickup_position + 1, route_length + 1):
        delivery_route = Route(
            vehicle=route_with_pickup.vehicle,
            stops=list(route_with_pickup.stops),
        )
        delivery_route.stops.insert(j, delivery_stop)

        delivery_route_state = RouteState(
            darp_config=darp_instance.darp_config,
            route=delivery_route,
            requests=darp_instance.requests,
            travel_time=darp_instance.travel_time,
            travel_distance=darp_instance.travel_distance,
            early_exit_on_violation=use_early_exit,
        )
        delivery_route_state.recompute()

        if not delivery_route_state.is_feasible():
            continue

        delivery_objective_value = compute_route_objective_function(delivery_route_state)
        delivery_delta = delivery_objective_value - best_pickup_route_objective_value

        if delivery_delta < best_whole_delta:
            best_whole_delta = delivery_delta
            best_whole_route = delivery_route

    if best_whole_route is None:
        return None

    return best_route_index, best_whole_route


def _greedy_construction_routes_with_order(
        *,
        darp_instance: DarpInstance,
        request_order: list[UUID],
        use_early_exit: bool = False,
) -> DarpSolution:
    """
    Gemeinsame Kernfunktion für verschiedene Varianten der Greedy-Konstruktionsheuristik.

    Ablauf:

    1. Initialisierung der Fahrzeugrouten
    2. Sequenzielle Bearbeitung der Anfragen durch die Methode best_insertion_for_request()
    3. Speichern von erfolgreichen und nicht erfolgreichen Anfragen sowie den entstandenen Routen
    4. Rückgabe des resultierenden DarpSolution-Objekts
    """
    routes: list[Route] = [
        Route(vehicle=vehicle, stops=[])
        for vehicle in darp_instance.vehicles
    ]

    served_requests: list[UUID] = []
    unserved_requests: list[UUID] = []

    for request_id in request_order:
        result = best_insertion_for_request(
            routes=routes,
            request_id=request_id,
            darp_instance=darp_instance,
            use_early_exit=use_early_exit,
        )

        if result is None:
            unserved_requests.append(request_id)
            continue

        route_index, new_route = result
        routes[route_index] = new_route
        served_requests.append(request_id)

    return DarpSolution(
        darp_instance=darp_instance,
        routes=routes,
        served_requests=served_requests,
        unserved_requests=unserved_requests,
    )


def sort_by_earliest_desired_pickup_time(*, darp_instance: DarpInstance) -> list[UUID]:
    """
    Sortiert die Anfrage-IDs aufsteigend nach gewünschter Abholzeit.

    Hinweis: In der Arbeit wurde die Vorsortierung für den spätest möglichen Abholzeitpunkt gewählt. Hier wird der
    gewünschte Abholzeitpunkt als Sortierungsargument gewählt. Dies liegt daran, dass auf den gewünschten Abholzeitpunkt
    direkt zugegriffen werden, während der spätest möglichen Abholzeitpunkt pro Anfrage abhängig von der DarpConfig
    berechnet werden müsste.
    Der spätest möglichen Abholzeitpunkt setzt aber aus dem gewünschten Abholzeitpunkt + pickup_buffer aus der DarpConfig
    zusammen. Da der pickup_buffer eine fest definierte Minutendauer ist, kann hier analog der gewünschte Abholzeitpunkt
    verwendet werden.
    """
    return sorted(
        darp_instance.request_order,
        key=lambda request_id: darp_instance.requests[request_id].desired_pickup_time,
    )


def greedy_construction_routes(*, darp_instance: DarpInstance) -> DarpSolution:
    """
    Baseline-Greedy-Verfahren ohne Vorsortierung und ohne Early Exit.
    """
    return _greedy_construction_routes_with_order(
        darp_instance=darp_instance,
        request_order=darp_instance.request_order,
        use_early_exit=False,
    )


def greedy_construction_routes_time_restrictive_scenario(
        *,
        darp_instance: DarpInstance,
) -> DarpSolution:
    """
    Erweiterte Greedy-Variante mit Vorsortierung und early-exit-Mechanismus

    Vorsortierung wird nach der frühsten gewünschten Abholzeit durchgeführt

    Early-Exit-Mechanismus bricht die Zulässigkeitsprüfung und die Berechnung der Routen-Metriken frühzeitig ab, sobald
    eine Nebenbedingung des DARPs verletzt wird.
    """
    sorted_request_order = sort_by_earliest_desired_pickup_time(
        darp_instance=darp_instance,
    )

    return _greedy_construction_routes_with_order(
        darp_instance=darp_instance,
        request_order=sorted_request_order,
        use_early_exit=True,
    )
