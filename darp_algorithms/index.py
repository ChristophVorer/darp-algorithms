from __future__ import annotations

from datetime import datetime, timedelta

from darp_algorithms.core import ConstraintConfig, DarpConfig
from darp_algorithms.core.greedy_heuristic import (
    greedy_construction_routes,
    greedy_construction_routes_time_restrictive_scenario,
)
from darp_algorithms.core.local_search import local_search_improvement
from darp_algorithms.core.objective_config import ObjectiveConfig
from darp_algorithms.core.solution_metrics import compute_solution_metrics
from darp_algorithms.evaluation.evaluations_mapper import (
    build_evaluation_result,
    print_evaluation_result,
    write_evaluation_result_to_csv_file,
)
from darp_algorithms.infrastructure.darp_instance_generator import DarpInstanceGenerator
from darp_algorithms.infrastructure.osrm_matrix_provider import OsrmMatrixProvider
from darp_algorithms.scenario import RequestGenerator, ScenarioConfig, VehicleGenerator


def build_darp_config_basic() -> DarpConfig:
    return DarpConfig(
        vehicle_capacity=20,
        service_duration=timedelta(seconds=30),
        pickup_buffer=timedelta(minutes=15),
        objective_config=ObjectiveConfig(
            use_total_travel_time=True,
            travel_time_weight=4.0,
            use_travel_cost=True,
            travel_cost_weight=1.0,
            cost_per_kilometer=2.2,
        ),
        constraint_config=ConstraintConfig(
            use_max_ride_time=False
        ),
    )


def build_darp_config_time_restrictive() -> DarpConfig:
    return DarpConfig(
        vehicle_capacity=20,
        service_duration=timedelta(seconds=90),
        pickup_buffer=timedelta(minutes=3),
        objective_config=ObjectiveConfig(
            use_total_travel_time=True,
            travel_time_weight=4.0,
            use_travel_cost=True,
            travel_cost_weight=1.0,
            cost_per_kilometer=2.2,
        ),
        constraint_config=ConstraintConfig(
            use_max_ride_time=False
        ),
    )


def build_scenario_config_basic(*, random_seed: int) -> ScenarioConfig:
    return ScenarioConfig(
        random_seed=random_seed,
        number_of_requests=20,
        number_of_vehicles=4,
        scenario_start_time=datetime(2026, 3, 5, 8, 0, 0),
        scenario_end_time=datetime(2026, 3, 5, 16, 0, 0),
    )


def build_scenario_config_time_restrictive(*, random_seed: int) -> ScenarioConfig:
    return ScenarioConfig(
        random_seed=random_seed,
        number_of_requests=20,
        number_of_vehicles=4,
        scenario_start_time=datetime(2026, 3, 5, 10, 0, 0),
        scenario_end_time=datetime(2026, 3, 5, 12, 0, 0),
    )


def run_single_experiment(
        *,
        random_seed: int,
) -> list:
    # scenario_name = "basic"
    # scenario_config = build_scenario_config_basic(random_seed=random_seed)
    # darp_config = build_darp_config_basic()

    scenario_name = "time_restrictive"
    scenario_config = build_scenario_config_time_restrictive(random_seed=random_seed)
    darp_config = build_darp_config_time_restrictive()

    requests = RequestGenerator(
        scenario_config=scenario_config,
    ).generate_requests()

    vehicles = VehicleGenerator(
        scenario_config=scenario_config,
    ).generate_vehicles()

    darp_instance = DarpInstanceGenerator(
        osrm_matrix_provider=OsrmMatrixProvider(),
    ).generate_instance(
        darp_config=darp_config,
        vehicles=vehicles,
        requests=requests,
    )

    experiment_name = (
        f"seed_{random_seed}"
        f"_req_{scenario_config.number_of_requests}"
        f"_veh_{scenario_config.number_of_vehicles}"
    )

    results = []

    baseline_solution = greedy_construction_routes(
        darp_instance=darp_instance,
    )
    baseline_metrics = compute_solution_metrics(
        darp_solution=baseline_solution,
    )
    baseline_result = build_evaluation_result(
        experiment_name=experiment_name,
        scenario_name=scenario_name,
        solver_name="greedy_baseline",
        random_seed=random_seed,
        scenario_config=scenario_config,
        darp_config=darp_config,
        solution_metrics=baseline_metrics,
    )
    results.append(baseline_result)

    refined_solution = greedy_construction_routes_time_restrictive_scenario(
        darp_instance=darp_instance,
    )
    refined_metrics = compute_solution_metrics(
        darp_solution=refined_solution,
    )
    refined_result = build_evaluation_result(
        experiment_name=experiment_name,
        scenario_name=scenario_name,
        solver_name="greedy_refined",
        random_seed=random_seed,
        scenario_config=scenario_config,
        darp_config=darp_config,
        solution_metrics=refined_metrics,
    )
    results.append(refined_result)

    local_search_solution = local_search_improvement(
        darp_solution=refined_solution
    )
    local_search_metrics = compute_solution_metrics(
        darp_solution=local_search_solution,
    )
    local_search_result = build_evaluation_result(
        experiment_name=experiment_name,
        scenario_name=scenario_name,
        solver_name="local_search",
        random_seed=random_seed,
        scenario_config=scenario_config,
        darp_config=darp_config,
        solution_metrics=local_search_metrics,
    )

    results.append(local_search_result)

    return results


def main() -> None:
    seeds = list(range(20))
    all_results = []

    for seed in seeds:
        experiment_results = run_single_experiment(random_seed=seed)
        all_results.extend(experiment_results)

        for result in experiment_results:
            print_evaluation_result(result)

    write_evaluation_result_to_csv_file(
        results=all_results,
        output_path="artifacts/evaluation_results.csv",
    )


if __name__ == "__main__":
    main()
