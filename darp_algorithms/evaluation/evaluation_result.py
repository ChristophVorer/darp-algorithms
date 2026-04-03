from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    """
    Klasse zum Kapseln der Evaluationsparameter

    Enthält Metriken über die Durchführung eines Experiments auf genau einem Seed für genau einen Solver.
    """
    # Experiment-Id - Zum Trennen der einzelnen Solver-Durchläufe
    experiment_name: str

    # Szenario-Name - "basic", "time-restrictive" und "res-n-rt-restrictive"
    scenario_name: str

    # Solver-Name
    solver_name: str

    # Szenario-Attribute
    random_seed: int
    number_of_requests: int
    number_of_vehicles: int
    vehicle_capacity: int

    # Solution-Attribute
    number_of_routes: int
    number_of_requests_total: int
    number_of_requests_served: int
    number_of_requests_unserved: int
    percentage_of_served_requests: float

    raw_travel_time_part: float
    raw_travel_cost_part: float
    raw_capacity_balancing_part: float

    weighted_travel_time_part: float
    weighted_travel_cost_part: float
    weighted_capacity_balancing_part: float

    total_travel_time: float
    total_travel_distance: float
    total_objective_value: float
    number_of_feasible_routes: int
    number_of_infeasible_routes: int
    number_of_total_violations: int
    objective_value_per_served_request: float
    travel_time_per_served_request: float
    travel_distance_per_served_request: float
