from dataclasses import dataclass

from .darp_solution import DarpSolution
from .route_objective import compute_route_objective_function
from .route_state import RouteState


@dataclass(frozen=True)
class SolutionMetrics:
    number_of_routes: int
    number_of_requests_total: int
    number_of_requests_served: int
    number_of_requests_unserved: int
    percentage_of_served_requests: float

    total_travel_time: float
    total_travel_distance: float
    total_objective_value: float

    number_of_feasible_routes: int
    number_of_infeasible_routes: int
    number_of_total_violations: int

    objective_value_per_served_request: float
    travel_time_per_served_request: float
    travel_distance_per_served_request: float


def compute_solution_metrics(
        *,
        darp_solution: DarpSolution
) -> SolutionMetrics:
    darp_instance = darp_solution.darp_instance
    total_travel_time_seconds = 0.0
    total_travel_distance = 0.0
    total_objective_value = 0.0
    num_feasible_routes = 0
    num_infeasible_routes = 0
    num_total_violations = 0

    for route in darp_solution.routes:
        route_state = RouteState(
            darp_config=darp_instance.darp_config,
            route=route,
            requests=darp_instance.requests,
            travel_time=darp_instance.travel_time,
            travel_distance=darp_instance.travel_distance,
        )
        route_state.recompute()

        total_travel_time_seconds += route_state.total_travel_time.total_seconds()
        total_travel_distance += route_state.total_travel_distance
        total_objective_value += compute_route_objective_function(route_state)
        num_total_violations += len(route_state.violations)

        if route_state.is_feasible():
            num_feasible_routes += 1
        else:
            num_infeasible_routes += 1

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

    if number_of_requests_total > 0:
        objective_value_per_served_request = (total_objective_value / number_of_requests_total)
        travel_time_per_served_request = (total_travel_time_seconds / number_of_requests_total)
        travel_distance_per_served_request = (total_travel_distance / number_of_requests_total)

    return SolutionMetrics(
        number_of_routes=len(darp_solution.routes),
        number_of_requests_total=number_of_requests_total,
        number_of_requests_served=number_of_requests_served,
        number_of_requests_unserved=number_of_requests_unserved,
        percentage_of_served_requests=percentage_of_served_requests,
        total_travel_time=total_travel_time_seconds,
        total_travel_distance=total_travel_distance,
        total_objective_value=total_objective_value,
        number_of_feasible_routes=num_feasible_routes,
        number_of_infeasible_routes=num_infeasible_routes,
        number_of_total_violations=num_total_violations,
        objective_value_per_served_request=objective_value_per_served_request,
        travel_time_per_served_request=travel_time_per_served_request,
        travel_distance_per_served_request=travel_distance_per_served_request,
    )
