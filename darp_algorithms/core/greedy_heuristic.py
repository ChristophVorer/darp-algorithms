from __future__ import annotations

from typing import Optional
from uuid import UUID

from darp_algorithms.domain.enums.stop_kind import StopKind
from darp_algorithms.domain.route import Route
from darp_algorithms.domain.stop import Stop

from .darp_instance import DarpInstance
from .darp_solution import DarpSolution
from .route_objective import compute_solution_objective_function
from .route_state import RouteState


def compute_routestate_and_route_with_insertion(
        *,
        route: Route,
        insert_position: int,
        stop: Stop,
        darp_config,
        darp_instance,
        use_early_exit: bool,
) -> tuple[RouteState, Route]:
    """
    Fügt anhand der Parameter den übergebenen Stopp in die gegebene Route ein und berechnet die zugehörigen
    Routen-Metriken.
    """

    updated_route = Route(
        vehicle=route.vehicle,
        stops=list(route.stops),
    )
    updated_route.stops.insert(insert_position, stop)

    route_state = RouteState(
        darp_config=darp_config,
        route=updated_route,
        requests=darp_instance.requests,
        travel_time=darp_instance.travel_time,
        travel_distance=darp_instance.travel_distance,
        early_exit_on_violation=use_early_exit,
    )
    route_state.recompute()

    return route_state, updated_route


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


    Gibt, sofern eine zulässige Lösung gefunden wurde, das Tupel aus dem Routenindex und aktualisierter Route aus, die
    zuvor als beste Einfügeposition bestimmt wurde. Andernfalls wird None zurückgegeben.
    """

    darp_config = darp_instance.darp_config
    objective_config = darp_config.objective_config
    request = darp_instance.requests[request_id]

    pickup_stop = Stop(
        kind=StopKind.PICKUP,
        request_id=request_id,
        location=request.pickup
    )
    delivery_stop = Stop(
        kind=StopKind.DELIVERY,
        request_id=request_id,
        location=request.delivery
    )

    best_pickup_route: Optional[Route] = None
    best_pickup_position = -1
    best_route_index = -1
    best_pickup_solution_objective_value = float("inf")

    best_whole_route: Optional[Route] = None
    best_whole_solution_objective_value = float("inf")

    # Berechne die aktuellen RouteStates der Ausgangslösung
    current_route_states: list[RouteState] = []
    for route in routes:
        route_state = RouteState(
            darp_config=darp_config,
            route=route,
            requests=darp_instance.requests,
            travel_time=darp_instance.travel_time,
            travel_distance=darp_instance.travel_distance,
            early_exit_on_violation=use_early_exit,
        )
        route_state.recompute()
        current_route_states.append(route_state)

    # Phase 1: Ermittle die beste Position für den Abholknoten über alle Routen
    for route_index, route in enumerate(routes):
        route_length = len(route.stops)

        for insert_position in range(route_length + 1):
            pickup_state, pickup_route = compute_routestate_and_route_with_insertion(
                route=route,
                insert_position=insert_position,
                stop=pickup_stop,
                darp_config=darp_config,
                darp_instance=darp_instance,
                use_early_exit=use_early_exit,
            )

            # Überprüfung, ob die entstandene Route zulässig ist
            if not pickup_state.is_feasible():
                continue

            # Bilde die Liste an RouteStates für die Kandidaten-Lösung
            candidate_route_states = list(current_route_states)
            candidate_route_states[route_index] = pickup_state

            # Berechne den Zielfunktionswert für die Kandidaten-Lösung
            candidate_solution_objective_value = compute_solution_objective_function(
                route_states=candidate_route_states,
                objective_config=objective_config
            )

            # Wenn die aktuelle Kandidatenlösung einen niedrigeren Zielfunktionswert
            # als die aktuell beste Pickup-Kandidatenlösung besitzt, überschreibe diese
            if candidate_solution_objective_value < best_pickup_solution_objective_value:
                best_pickup_position = insert_position
                best_pickup_route = pickup_route
                best_pickup_solution_objective_value = candidate_solution_objective_value
                best_route_index = route_index

    # Konnte keine zulässige Einfügeposition für den Abholknoten bestimmt werden, wird None zurückgegeben
    if best_pickup_route is None:
        return None

    # Phase 2: Ermittle die beste Einfügeposition für den Zielknoten der Anfrage innerhalb derselben Route des
    # Abholknotens
    route_with_pickup = best_pickup_route
    route_length = len(route_with_pickup.stops)
    for delivery_positon in range(best_pickup_position + 1, route_length + 1):
        delivery_state, delivery_route = compute_routestate_and_route_with_insertion(
            route=route_with_pickup,
            insert_position=delivery_positon,
            stop=delivery_stop,
            darp_config=darp_config,
            darp_instance=darp_instance,
            use_early_exit=use_early_exit,
        )

        # Überprüfung, ob die entstandene Route zulässig ist
        if not delivery_state.is_feasible():
            continue

        # Bilde die Liste an RouteStates für die Kandidaten-Lösung
        candidate_route_states = list(current_route_states)
        candidate_route_states[best_route_index] = delivery_state

        # Berechne den Zielfunktionswert für die Kandidaten-Lösung
        candidate_solution_objective_value = compute_solution_objective_function(
            route_states=candidate_route_states,
            objective_config=objective_config
        )

        # Wenn die aktuelle Kandidatenlösung einen niedrigeren Zielfunktionswert
        # als die aktuell beste vollständige Kandidatenlösung besitzt, überschreibe diese
        if candidate_solution_objective_value < best_whole_solution_objective_value:
            best_whole_solution_objective_value = candidate_solution_objective_value
            best_whole_route = delivery_route

    # Konnte keine zulässige Einfügeposition für den Zielknoten bestimmt werden, wird None zurückgegeben
    if best_whole_route is None:
        return None

    return best_route_index, best_whole_route


def greedy_construction_routes_with_order(
        *,
        darp_instance: DarpInstance,
        request_order: list[UUID],
        use_early_exit: bool = False,
) -> DarpSolution:
    """
    Gemeinsame Kernfunktion für verschiedene Varianten der Greedy-Konstruktionsheuristik.

    Ablauf:

    1. Initialisierung der Fahrzeugrouten
    2. Sequenzielle Bearbeitung der Anfragen durch die Methode `best_insertion_for_request()`
    3. Speichern von erfolgreichen und nicht erfolgreichen Anfragen sowie den entstandenen Routen
    4. Rückgabe des resultierenden DarpSolution-Objekts
    """

    # Initialisierung der Fahrzeugrouten
    routes: list[Route] = [
        Route(vehicle=vehicle, stops=[])
        for vehicle in darp_instance.vehicles
    ]

    served_requests: list[UUID] = []
    unserved_requests: list[UUID] = []

    for request_id in request_order:
        # Bestimme die beste Einfügeposition der Anfrage innerhalb der aktuellen Routenstruktur
        result = best_insertion_for_request(
            routes=routes,
            request_id=request_id,
            darp_instance=darp_instance,
            use_early_exit=use_early_exit,
        )

        # Konnte keine zulässige Einfügeposition gefunden werden, markiere die Anfrage als "nicht bedient"
        if result is None:
            unserved_requests.append(request_id)
            continue

        # Konnte eine zulässige Einfügeposition gefunden werden, markiere die Anfrage als "bedient" und aktualisiere die
        # aktuelle Routenstruktur
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

    Hinweis:
    In der Arbeit wurde die Vorsortierung für den spätest möglichen Abholzeitpunkt gewählt. Hier wird der gewünschte
    Abholzeitpunkt als Sortierungsargument gewählt. Dies liegt daran, dass auf den gewünschten Abholzeitpunkt direkt
    zugegriffen werden, während der spätest möglichen Abholzeitpunkt pro Anfrage abhängig von der DarpConfig berechnet
    werden müsste.
    Der spätest möglichen Abholzeitpunkt setzt aber aus dem gewünschten Abholzeitpunkt + pickup_buffer aus der
    DarpConfig zusammen. Da der pickup_buffer eine fest definierte Minutendauer ist, kann hier analog der gewünschte
    Abholzeitpunkt verwendet werden.
    """

    return sorted(
        darp_instance.request_order,
        key=lambda request_id: darp_instance.requests[request_id].desired_pickup_time,
    )


def greedy_construction_routes(*, darp_instance: DarpInstance) -> DarpSolution:
    """
    Baseline-Greedy-Verfahren ohne Vorsortierung und ohne Early Exit.
    """

    return greedy_construction_routes_with_order(
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

    Die Vorsortierung wird nach dem frühsten gewünschten Abholzeit durchgeführt

    Early-Exit-Mechanismus:
    Die Zulässigkeitsprüfung und die Berechnung der Routen-Metriken wird frühzeitig abgebrochen, sobald eine
    Nebenbedingung des DARPs verletzt wird.
    """

    sorted_request_order = sort_by_earliest_desired_pickup_time(
        darp_instance=darp_instance,
    )

    return greedy_construction_routes_with_order(
        darp_instance=darp_instance,
        request_order=sorted_request_order,
        use_early_exit=True,
    )
