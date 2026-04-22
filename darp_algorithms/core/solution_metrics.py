from dataclasses import dataclass

from .darp_solution import DarpSolution
from .route_objective import compute_capacity_imbalance, compute_solution_objective_function
from .route_state import RouteState


@dataclass(frozen=True)
class SolutionMetrics:
    """
    Definiert alle lösungsbasierten und für die spätere Evaluation relevanten Metriken
    """

    # Routen-Metriken
    number_of_routes: int
    number_of_requests_total: int
    number_of_requests_served: int
    number_of_requests_unserved: int
    percentage_of_served_requests: float

    # Ungewichtete Zielfunktionsanteile
    raw_travel_time_part: float
    raw_travel_cost_part: float
    raw_capacity_balancing_part: float

    # Gewichtete Zielfunktionsanteile
    weighted_travel_time_part: float
    weighted_travel_cost_part: float
    weighted_capacity_balancing_part: float

    # Fahrtzeit-Metriken
    total_travel_time: float
    travel_time_per_served_request: float

    # Fahrtdistanz-Metriken
    total_travel_distance: float
    travel_distance_per_served_request: float

    # Zielfunktionswert-Metriken
    total_objective_value: float
    objective_value_per_served_request: float

    # Metriken über zulässige und unzulässige Routen
    number_of_feasible_routes: int
    number_of_infeasible_routes: int
    number_of_total_violations: int


def compute_solution_metrics(
        *,
        darp_solution: DarpSolution
) -> SolutionMetrics:
    """
    Berechnet aus einer übergebenen DarpSolution die lösungsbasierten und für die spätere Evaluation relevanten
    Metriken.
    """

    darp_instance = darp_solution.darp_instance
    darp_config = darp_instance.darp_config
    objective_config = darp_config.objective_config

    total_travel_time_seconds = 0.0
    total_travel_distance = 0.0
    num_feasible_routes = 0
    num_infeasible_routes = 0
    num_total_violations = 0

    # Berechnung der RouteStates aller in der Lösung enthaltenen Routen
    route_states: list[RouteState] = []
    for route in darp_solution.routes:
        route_state = RouteState(
            darp_config=darp_config,
            route=route,
            requests=darp_instance.requests,
            travel_time=darp_instance.travel_time,
            travel_distance=darp_instance.travel_distance,
            early_exit_on_violation=False,
        )
        route_state.recompute()
        route_states.append(route_state)

        total_travel_time_seconds += route_state.total_travel_time.total_seconds()
        total_travel_distance += route_state.total_travel_distance
        num_total_violations += len(route_state.violations)

        if route_state.is_feasible():
            num_feasible_routes += 1
        else:
            num_infeasible_routes += 1

    # Berechnung des Zielfunktionswerts der übergebenen Lösung
    total_objective_value = compute_solution_objective_function(
        route_states=route_states,
        objective_config=objective_config,
    )

    number_of_requests_total = len(darp_instance.requests)
    number_of_requests_served = len(darp_solution.served_requests)
    number_of_requests_unserved = len(darp_solution.unserved_requests)

    percentage_of_served_requests = 0.0
    if number_of_requests_total > 0:
        percentage_of_served_requests = (
                number_of_requests_served / number_of_requests_total * 100
        )

    objective_value_per_served_request = 0.0
    travel_time_per_served_request = 0.0
    travel_distance_per_served_request = 0.0

    if number_of_requests_served > 0:
        objective_value_per_served_request = (
                total_objective_value / number_of_requests_served
        )
        travel_time_per_served_request = (
                total_travel_time_seconds / number_of_requests_served
        )
        travel_distance_per_served_request = (
                total_travel_distance / number_of_requests_served
        )

    # Roh-Anteile der Optimierungsziele an der Zielfunktion.
    # Für die Analyse der Gewichtungsparameter in der Zielfunktion, werden diese Anteile immer berechnet, egal ob das
    # jeweilige Optimierungsziel aktiviert ist oder nicht.
    raw_travel_time_part = total_travel_time_seconds
    raw_travel_cost_part = objective_config.cost_per_kilometer * total_travel_distance
    raw_capacity_balancing_part = compute_capacity_imbalance(route_states=route_states)

    weighted_travel_time_part = raw_travel_time_part * objective_config.travel_time_weight
    weighted_travel_cost_part = raw_travel_cost_part * objective_config.travel_cost_weight
    weighted_capacity_balancing_part = raw_capacity_balancing_part * objective_config.capacity_balancing_weight

    return SolutionMetrics(
        number_of_routes=len(darp_solution.routes),
        number_of_requests_total=number_of_requests_total,
        number_of_requests_served=number_of_requests_served,
        number_of_requests_unserved=number_of_requests_unserved,
        percentage_of_served_requests=percentage_of_served_requests,
        raw_travel_time_part=raw_travel_time_part,
        raw_travel_cost_part=raw_travel_cost_part,
        raw_capacity_balancing_part=raw_capacity_balancing_part,
        weighted_travel_time_part=weighted_travel_time_part,
        weighted_travel_cost_part=weighted_travel_cost_part,
        weighted_capacity_balancing_part=weighted_capacity_balancing_part,
        total_travel_time=total_travel_time_seconds,
        travel_time_per_served_request=travel_time_per_served_request,
        total_travel_distance=total_travel_distance,
        travel_distance_per_served_request=travel_distance_per_served_request,
        total_objective_value=total_objective_value,
        objective_value_per_served_request=objective_value_per_served_request,
        number_of_feasible_routes=num_feasible_routes,
        number_of_infeasible_routes=num_infeasible_routes,
        number_of_total_violations=num_total_violations,
    )
