from __future__ import annotations

from uuid import UUID

from darp_algorithms.domain.route import Route
from .darp_solution import DarpSolution
from .greedy_heuristic import best_insertion_for_request
from .solution_metrics import compute_solution_metrics


def _remove_request_from_routes(*, routes: list[Route], request_id: UUID) -> list[Route]:
    """
    Entfernt eine übergebene Anfrage aus der ihr zugeteilten Route.

    Dazu wird zunächst die Route der Anfrage aus einer Liste von Routen identifziert und dann sowohl der Abhol- als auch
    der Zielknoten entfernt.
    :param routes:
    :param request_id:
    :return:
    """
    new_routes: list[Route] = []

    # Filterung die übergebenen Routen
    for route in routes:
        # Filtere die Stopps aus den Routen, die mit der übergebenen Request-Id übereinstimmen
        filtered_stops = [
            stop for stop in route.stops
            if stop.request_id != request_id
        ]
        new_routes.append(
            Route(
                vehicle=route.vehicle,
                stops=filtered_stops,
            )
        )

    # Gebe die aktualisierten Routen zurück
    return new_routes


def _insert_request_into_routes(
        *,
        routes: list[Route],
        darp_solution: DarpSolution,
        request_id: UUID,
) -> list[Route] | None:
    """
    Fügt eine Anfrage in eine Liste von Routen ein.

    Es werden dazu alle möglichen Einfügepositionen für die Anfrage in der Menge der Routen betrachtet. Dabei wird das
    Positionspaar, welches den Zielfunktionswert der Lösung minimiert ausgewählt.
    :param routes:
    :param darp_solution:
    :param request_id:
    :return:
    """

    # Kopiere die Routen der Lösung
    new_routes = [
        Route(vehicle=route.vehicle, stops=list(route.stops))
        for route in routes
    ]

    # Hier wird für die Bestimmung des Positionspaares die Funktion best_insertion_for_request() verwendet, die auch
    # für die sequenzielle Einfügung der Anfragen bei den Greedy-Heuristiken verantwortlich ist.
    best_insertion = best_insertion_for_request(
        routes=new_routes,
        request_id=request_id,
        darp_instance=darp_solution.darp_instance,
        use_early_exit=False,
    )

    # Wenn keine zulässige Lösung gefunden werden konnte, wird None zurückgegeben
    if best_insertion is None:
        return None

    # Ansonsten werden die neu entstandenen Routen der Fahrzeuge nach Einfügung der Anfrage zurückgegeben
    route_index, new_route = best_insertion
    new_routes[route_index] = new_route

    return new_routes


def relocate_request(*, darp_solution: DarpSolution, request_id: UUID) -> DarpSolution | None:
    """
    Die Funktion definiert einen Relocate-Operator für das Local-Search-Verfahren.

    Zunächst entfernt der Relocate-Operator eine Anfrage aus einer übergebenen Lösung mithilfe von
    _remove_request_from_routes(). Im Anschluss fügt der Relocate-Operator diese Anfrage mithilfe von
    _insert_request_into_routes wieder in Lösung ein.
    :param darp_solution:
    :param request_id:
    :return:
    """
    darp_instance = darp_solution.darp_instance

    # Entfernen der Anfrage aus der Lösung
    relocate_routes = _remove_request_from_routes(
        routes=darp_solution.routes,
        request_id=request_id,
    )

    # Hinzufügen der Anfrage in die besten Einfügepositionen für Abhol- und Zielknoten
    relocate_routes = _insert_request_into_routes(
        routes=relocate_routes,
        darp_solution=darp_solution,
        request_id=request_id,
    )

    # Wenn keine zulässige Lösung gefunden werden konnte, wird None zurückgegeben.
    # Dieser Fall kann aber in der Praxis eigentlich nicht eintreten, da aus einer zulässigen Lösung zuvor eine Anfrage
    # entfernt wurde. Es muss also zumindest ein zulässiges Positionspaar für die Einfügung derselben Anfrage
    # existieren, nämlich genau die Positionen für Abhol- und Zielknoten der Anfrage vor Entfernung durch
    # _remove_request_from_routes()
    if relocate_routes is None:
        return None

    # Ansonsten wird die neu entstandene Lösung zurückgegeben
    return DarpSolution(
        darp_instance=darp_instance,
        routes=relocate_routes,
        served_requests=list(darp_solution.served_requests),
        unserved_requests=list(darp_solution.unserved_requests),
    )


def exchange_requests(
        *,
        darp_solution: DarpSolution,
        request_id_1: UUID,
        request_id_2: UUID,
) -> DarpSolution | None:
    darp_instance = darp_solution.darp_instance

    exchange_routes = _remove_request_from_routes(
        routes=darp_solution.routes,
        request_id=request_id_1,
    )

    exchange_routes = _remove_request_from_routes(
        routes=exchange_routes,
        request_id=request_id_2,
    )

    exchange_routes = _insert_request_into_routes(
        routes=exchange_routes,
        darp_solution=darp_solution,
        request_id=request_id_1,
    )

    # Wenn keine zulässige Lösung gefunden werden konnte, wird None zurückgegeben.
    # Dieser Fall kann an dieser Stelle in der Praxis eigentlich nicht eintreten, da aus einer zulässigen Lösung zuvor
    # zwei Anfragen entfernt wurden. Es muss also zumindest ein zulässiges Positionspaar für die Einfügung existieren,
    # nämlich genau die Positionen für Abhol- und Zielknoten der Anfrage vor Entfernung durch
    # _remove_request_from_routes()
    if exchange_routes is None:
        return None

    exchange_routes = _insert_request_into_routes(
        routes=exchange_routes,
        darp_solution=darp_solution,
        request_id=request_id_2,
    )

    # Durch die sequenzielle Wiedereinfügung der Anfragen, kann bei der Ermittlung der besten Einfügeposition für die
    # zweite Anfrage eventuell None zurückgegeben werden. Denn abhängig davon, wie die erste Anfrage erneut der Lösung
    # hinzugefügt wurde, existiert potenziell keine valides Positionspaar mehr zur Wiedereinfügung der zweiten Anfrage.
    # Daher kann _insert_request_into_routes() auch None zurückgeben. In diesem Fall gibt auch exchange_requests()
    # insgesamt None zurück.
    if exchange_routes is None:
        return None

    return DarpSolution(
        darp_instance=darp_instance,
        routes=exchange_routes,
        served_requests=list(darp_solution.served_requests),
        unserved_requests=list(darp_solution.unserved_requests),
    )


def local_search_improvement(*, darp_solution: DarpSolution) -> DarpSolution:
    best_solution = DarpSolution(
        darp_instance=darp_solution.darp_instance,
        routes=list(darp_solution.routes),
        served_requests=list(darp_solution.served_requests),
        unserved_requests=list(darp_solution.unserved_requests),
    )

    solution_metrics = compute_solution_metrics(darp_solution=best_solution)
    best_solution_delta = solution_metrics.total_objective_value
    while True:
        improvement: bool = False
        requests = list(best_solution.served_requests)
        for request_id in requests:
            candidate_solution = relocate_request(
                darp_solution=best_solution,
                request_id=request_id,
            )

            if candidate_solution is None:
                continue

            candidate_solution_metrics = compute_solution_metrics(darp_solution=candidate_solution)
            candidate_solution_delta = candidate_solution_metrics.total_objective_value
            if candidate_solution_delta < best_solution_delta:
                best_solution = candidate_solution
                best_solution_delta = candidate_solution_delta
                improvement = True
                break

        if improvement:
            continue

        for i in range(len(requests)):
            for j in range(i + 1, len(requests)):
                request_id_1 = requests[i]
                request_id_2 = requests[j]

                candidate_solution = exchange_requests(
                    darp_solution=best_solution,
                    request_id_1=request_id_1,
                    request_id_2=request_id_2
                )

                if candidate_solution is None:
                    continue

                candidate_solution_metrics = compute_solution_metrics(darp_solution=candidate_solution)
                candidate_solution_delta = candidate_solution_metrics.total_objective_value
                if candidate_solution_delta < best_solution_delta:
                    best_solution = candidate_solution
                    best_solution_delta = candidate_solution_delta
                    improvement = True
                    break

            if improvement:
                break

        if improvement:
            continue

        break

    return best_solution
