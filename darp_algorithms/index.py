from __future__ import annotations

from datetime import datetime, timedelta

from darp_algorithms.core import ConstraintConfig, DarpConfig, DarpInstance
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
from darp_algorithms.infrastructure.osrm_matrix_provider import OsrmMatrixProvider, OsrmMatrixValidationException
from darp_algorithms.scenario import RequestGenerator, ScenarioConfig, VehicleGenerator


def build_darp_config_basic() -> DarpConfig:
    """
    Gibt die DarpConfig für ein Basis-Szenario zurück.

    Im Ausgangs-Szenario gilt Folgendes:

    - Keine Fahrtzeit-Beschränkung
    - Weite Zeitfenster an den Abholknoten
    - Fahrzeug-Kapazitäten nicht bindend
    - Zwei Optimierungsziele: Minimierung der Gesamt-Fahrtzeit und der Gesamt-Fahrtkosten

    :return:
    """

    return DarpConfig(
        vehicle_capacity=100,
        service_duration=timedelta(seconds=10),
        pickup_buffer=timedelta(minutes=20),
        objective_config=ObjectiveConfig(
            cost_per_kilometer=0.8,
            use_total_travel_time=True,
            use_travel_cost=True,
            use_capacity_balancing=False,
            travel_time_weight=1.0,
            travel_cost_weight=110
        ),
        constraint_config=ConstraintConfig(
            use_max_ride_time=False
        ),
    )


def build_darp_config_time_restrictive() -> DarpConfig:
    """
    Gibt die DarpConfig für ein zeitlich restriktives Szenario zurück.

    Im zeitlich restriktiven Szenario gilt Folgendes:

    - Enge Zeitfenster an den Abholknoten durch erhöhter Service-Zeiten und eines kleineren Pickup-Puffers
    - Keine Fahrtzeit-Beschränkung
    - Fahrzeug-Kapazitäten weiterhin nicht bindend
    - Zwei Optimierungsziele: Minimierung der Gesamt-Fahrtzeit und der Gesamt-Fahrtkosten

    :return:
    """

    return DarpConfig(
        vehicle_capacity=100,
        service_duration=timedelta(seconds=90),
        pickup_buffer=timedelta(minutes=3),
        objective_config=ObjectiveConfig(
            cost_per_kilometer=0.8,
            use_total_travel_time=True,
            use_travel_cost=True,
            use_capacity_balancing=False,
            travel_time_weight=1.0,
            travel_cost_weight=110,
        ),
        constraint_config=ConstraintConfig(
            use_max_ride_time=False
        ),
    )


def build_darp_config_resource_restrictive() -> DarpConfig:
    """
    Gibt die DarpConfig für ein ressourcen restriktives Szenario zurück. Es baut auf den zeitlich restriktiven Szenario
    auf und erweitert es zusätzlich im kapazitäts- und fahrtzeitbezogene Restriktionen und Auslastungsbalancing.

    Im ressourcen restriktiven Szenario gilt Folgendes:

    - Enge Zeitfenster an den Abholknoten durch höhere Service-Zeit und kleineren Pickup-Puffer
    - Maximale Fahrtzeit-Beschränkung
    - Fahrzeug-Kapazitäten werden bindend
    - Drei Optimierungsziele: Minimierung der Gesamt-Fahrtzeit, der Gesamt-Fahrtkosten und der Balancierung der
    Fahrzeugauslastung

    :return:
    """

    return DarpConfig(
        vehicle_capacity=6,
        service_duration=timedelta(seconds=90),
        pickup_buffer=timedelta(minutes=3),
        objective_config=ObjectiveConfig(
            cost_per_kilometer=0.8,
            use_total_travel_time=True,
            use_travel_cost=True,
            use_capacity_balancing=True,
            travel_time_weight=1.0,
            travel_cost_weight=110,
            capacity_balancing_weight=550000.0,
        ),
        constraint_config=ConstraintConfig(
            use_max_ride_time=True,
            mrt_factor=1.5
        ),
    )


def build_scenario_config_basic(*, random_seed: int) -> ScenarioConfig:
    """
    Gibt die ScenarioConfig für ein Basis-Szenario zurück.

    Im Ausgangs-Szenario gilt Folgendes:

    - Geringe Instanzgröße => wenige Fahrzeuge und Anfragen
    - Großzügiges Verhältnis von Anfragen und Service-Zeitraum

    :param random_seed:
    :return:
    """

    return ScenarioConfig(
        random_seed=random_seed,
        number_of_requests=30,
        number_of_vehicles=4,
        scenario_start_time=datetime(2026, 3, 5, 10, 0, 0),
        scenario_end_time=datetime(2026, 3, 5, 18, 0, 0),
        min_passengers=1,
        max_passengers=3,
    )


def build_scenario_config_time_restrictive(*, random_seed: int) -> ScenarioConfig:
    """
    Gibt die ScenarioConfig für ein zeitlich restriktives Szenario zurück.

    Im zeitlich restriktiven Szenario gilt Folgendes:

    - Weiterhin besteht eine geringe Instanzgröße, dementsprechend werden wenige Fahrzeuge und Anfragen generiert
    - Aber das Verhältnis von Anzahl der Anfragen zum Service-Zeitraum wird ungünstiger

    :param random_seed:
    :return:
    """

    return ScenarioConfig(
        random_seed=random_seed,
        number_of_requests=30,
        number_of_vehicles=4,
        scenario_start_time=datetime(2026, 3, 5, 10, 0, 0),
        scenario_end_time=datetime(2026, 3, 5, 13, 0, 0),
        min_passengers=1,
        max_passengers=3,
    )


def build_scenario_config_resource_restrictive(*, random_seed: int) -> ScenarioConfig:
    """
    Gibt die ScenarioConfig für ein ressourcen restriktives Szenario zurück.

    Im ressourcen restriktiven Szenario gilt Folgendes:

    - Weiterhin besteht eine geringe Instanzgröße, dementsprechend werden wenige Fahrzeuge und Anfragen generiert
    - Die Passagieranzahl pro Anfrage liegt nun zwischen 2 und 3 statt standardmäßig zwischen 1 und 3.

    :param random_seed:
    :return:
    """

    return ScenarioConfig(
        random_seed=random_seed,
        number_of_requests=30,
        number_of_vehicles=4,
        scenario_start_time=datetime(2026, 3, 5, 10, 0, 0),
        scenario_end_time=datetime(2026, 3, 5, 13, 0, 0),
        min_passengers=2,
        max_passengers=3,
    )


# ========================================
#      Szenario-Mapping
#
#   1. Basis-Szenario
#   2. Zeitlich restriktives Szenario
#   3. Ressourcen restriktives Szenario
#
# ========================================
SCENARIOS = {
    "1": {
        "name": "basic",
        "scenario_config": build_scenario_config_basic,
        "darp_config": build_darp_config_basic,
    },
    "2": {
        "name": "time_restrictive",
        "scenario_config": build_scenario_config_time_restrictive,
        "darp_config": build_darp_config_time_restrictive,
    },
    "3": {
        "name": "resource_restrictive",
        "scenario_config": build_scenario_config_resource_restrictive,
        "darp_config": build_darp_config_resource_restrictive,
    },
}


def build_reproducible_instance(
        *,
        scenario_name: str,
        base_seed: int,
        max_attempts: int = 10,
        retry_offset: int = 10000,
) -> tuple[ScenarioConfig, DarpConfig, DarpInstance]:
    """
    Baut für ein Szenario die entsprechende ScenarioConfig, DarpConfig und eine reproduzierbare DarpInstance.

    Die ScenarioConfig und DarpConfig wird aus dem SCENARIOS-Mapping gezogen.

    Die DarpInstance wird durch den RequestGenerator und den VehicleGenerator instanziiert. Für manche Orte kann OSRM
    aber keine Fahrtdistanzen oder Fahrtdauern berechnen. Wenn dies der Fall ist, wird versucht eine neue Instanz
    basierend auf dem alten Seed addiert mit einem Offset zu generieren.

    :param scenario_name:
    :param base_seed:
    :param max_attempts:
    :param retry_offset:
    :return:
    """
    for attempt in range(max_attempts):
        current_seed = base_seed + attempt * retry_offset

        # Bestimmung des Szenarios
        if scenario_name == "basic":
            scenario_config = build_scenario_config_basic(random_seed=current_seed)
            darp_config = build_darp_config_basic()
        elif scenario_name == "time_restrictive":
            scenario_config = build_scenario_config_time_restrictive(random_seed=current_seed)
            darp_config = build_darp_config_time_restrictive()
        elif scenario_name == "resource_restrictive":
            scenario_config = build_scenario_config_resource_restrictive(random_seed=current_seed)
            darp_config = build_darp_config_resource_restrictive()
        else:
            raise ValueError(f"Unbekanntes Szenario: {scenario_name}")

        # Generierung der Fahrzeuge und Anfragen
        requests = RequestGenerator(scenario_config=scenario_config).generate_requests()
        vehicles = VehicleGenerator(scenario_config=scenario_config).generate_vehicles()

        # Berechnung der DarpInstance aus den generierten Anfragen und Fahrzeugen
        try:
            darp_instance = (DarpInstanceGenerator(osrm_matrix_provider=OsrmMatrixProvider())
            .generate_instance(
                darp_config=darp_config,
                vehicles=vehicles,
                requests=requests,
            ))
            return scenario_config, darp_config, darp_instance

        # Tritt ein Fehler bei der Validierung der Matritzen auf, soll ein weiterer Versuch gestartet werden
        # Der entsprechende Fehler wird also nur abgefangen und in der Konsole ausgegeben.
        except OsrmMatrixValidationException as exception:
            print(exception)

    # Konnte keine Instanz generiert werden, wird soll ein Fehler ausgegeben werden
    raise RuntimeError(
        f"Es konnte nach {max_attempts} Versuchen keine routbare Instanz "
        f"für Szenario '{scenario_name}' und Basis-Seed {base_seed} erzeugt werden."
    )


def run_single_experiment(
        *,
        random_seed: int,
        scenario_name: str
) -> list:
    """
    Führt ein Experiment-Durchlauf für alle Solver auf derselben DarpInstance durch und speichert die Ergebnisse in der
    /artifacts/evaluation_results.csv

    :param random_seed:
    :param scenario_name:
    :return:
    """
    scenario_config, darp_config, darp_instance = build_reproducible_instance(
        scenario_name=scenario_name,
        base_seed=random_seed,
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
    """
    Erstellen eines Experiment-Settings per Konsolen Eingabe und anschließende Ausführung des Experiments.

    Auswahl-Möglichkeiten:

    1. Szenario
    2. Anzahl der Seeds (Experiment-Durchläufe)
    3. Start-Seed (Danach in aufsteigender Reihenfolge abhängig von der Anzahl der Seeds

    :return:
    """
    print("Wähle ein Szenario:")
    print("1 - basic")
    print("2 - time_restrictive")
    print("3 - resource_restrictive")

    scenario_choice = input("Eingabe: ").strip()
    scenario = SCENARIOS.get(scenario_choice)

    if scenario is None:
        print("Ungültige Auswahl")
        return

    num_seeds = int(input("Wie viele Seeds sollen verwendet werden? "))
    start_seed = int(input("Start-Seed: "))

    seeds = list(range(start_seed, start_seed + num_seeds))

    print(f"\nStarte Experimente für Szenario: {scenario['name']}")
    print(f"Seeds: {seeds}\n")

    all_results = []

    for seed in seeds:
        experiment_results = run_single_experiment(
            random_seed=seed,
            scenario_name=scenario["name"]
        )

        all_results.extend(experiment_results)

        for result in experiment_results:
            print_evaluation_result(result)

    write_evaluation_result_to_csv_file(
        results=all_results,
        output_path="artifacts/evaluation_results.csv",
    )


if __name__ == "__main__":
    main()
