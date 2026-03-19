import csv
from dataclasses import asdict
from pathlib import Path

from darp_algorithms.core import DarpConfig
from darp_algorithms.core.solution_metrics import SolutionMetrics
from darp_algorithms.evaluation.evaluation_result import EvaluationResult
from darp_algorithms.scenario import ScenarioConfig


def build_evaluation_result(
        *,
        experiment_name: str,
        scenario_name: str,
        solver_name: str,
        random_seed: int,
        scenario_config: ScenarioConfig,
        darp_config: DarpConfig,
        solution_metrics: SolutionMetrics,
) -> EvaluationResult:
    """
    Mappt die Parameter eines Solver-Durchlaufs auf ein EvaluationResult-Objekt.
    :param scenario_name:
    :param experiment_name:
    :param solver_name:
    :param random_seed:
    :param scenario_config:
    :param darp_config:
    :param solution_metrics:
    :return:
    """
    return EvaluationResult(
        experiment_name=experiment_name,
        scenario_name=scenario_name,
        solver_name=solver_name,
        random_seed=random_seed,
        number_of_requests=scenario_config.number_of_requests,
        number_of_vehicles=scenario_config.number_of_vehicles,
        vehicle_capacity=darp_config.vehicle_capacity,
        number_of_requests_served=solution_metrics.number_of_requests_served,
        number_of_requests_unserved=solution_metrics.number_of_requests_unserved,
        percentage_of_served_requests=solution_metrics.percentage_of_served_requests,
        raw_travel_time_part=solution_metrics.raw_travel_time_part,
        raw_travel_cost_part=solution_metrics.raw_travel_cost_part,
        raw_capacity_balancing_part=solution_metrics.raw_capacity_balancing_part,
        weighted_travel_time_part=solution_metrics.weighted_travel_time_part,
        weighted_travel_cost_part=solution_metrics.weighted_travel_cost_part,
        weighted_capacity_balancing_part=solution_metrics.weighted_capacity_balancing_part,
        number_of_routes=solution_metrics.number_of_routes,
        number_of_requests_total=solution_metrics.number_of_requests_total,
        number_of_feasible_routes=solution_metrics.number_of_feasible_routes,
        number_of_infeasible_routes=solution_metrics.number_of_infeasible_routes,
        number_of_total_violations=solution_metrics.number_of_total_violations,
        total_travel_time=solution_metrics.total_travel_time,
        total_travel_distance=solution_metrics.total_travel_distance,
        total_objective_value=solution_metrics.total_objective_value,
        objective_value_per_served_request=solution_metrics.objective_value_per_served_request,
        travel_time_per_served_request=solution_metrics.travel_time_per_served_request,
        travel_distance_per_served_request=solution_metrics.travel_distance_per_served_request,
    )


def write_evaluation_result_to_csv_file(
        *,
        results: list[EvaluationResult],
        output_path: str,
) -> None:
    if not results:
        raise ValueError("Die Result-Liste darf nicht leer sein.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(asdict(results[0]).keys()))

        if not file_exists:
            writer.writeheader()

        for result in results:
            writer.writerow(asdict(result))


def print_evaluation_result(result: EvaluationResult) -> None:
    print("\n=== Evaluation Result ===")
    print(f"Experiment-Name:                  {result.experiment_name}")
    print(f"Szenario:                         {result.scenario_name}")
    print(f"Solver:                           {result.solver_name}")
    print(f"Random seed:                      {result.random_seed}")
    print(f"Anfragen:                         {result.number_of_requests}")
    print(f"Fahrzeuge:                        {result.number_of_vehicles}")
    print(f"Fahrzeug-Kapazität:               {result.vehicle_capacity}")

    print("\nService:")
    print(f"  Bediente Anfragen:              {result.number_of_requests_served}")
    print(f"  Nicht bediente Anfragen:        {result.number_of_requests_unserved}")
    print(f"  Bediente Anfragen (in Prozent): {result.percentage_of_served_requests:.2f}%")

    print("\nRouten:")
    print(f"  Anzahl der Routen:              {result.number_of_routes}")
    print(f"  Zulässige Routen:               {result.number_of_feasible_routes}")
    print(f"  Unzulässige Routen:             {result.number_of_infeasible_routes}")
    print(f"  Insgesamte Violations:          {result.number_of_total_violations}")

    print("\nGesamt-Statistiken:")
    print(f"  Gesamt-Fahrtdauer:              {result.total_travel_time:.2f} s")
    print(f"  Gesamt-Fahrtdistanz:            {result.total_travel_distance:.2f} km")
    print(f"  Zielfunktionswert:              {result.total_objective_value:.2f}")

    print("\nStatistiken pro Anfrage:")
    print(f"  Zielfunktionswert pro Anfrage:  {result.objective_value_per_served_request:.2f} s")
    print(f"  Fahrtdistanz pro Anfrage:       {result.total_objective_value:.2f}")
    print(f"  Fahrtzeit pro Anfrage:          {result.travel_distance_per_served_request:.2f} km")
