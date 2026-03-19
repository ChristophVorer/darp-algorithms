import pandas as pandas
import matplotlib.pyplot as pyplot
from pathlib import Path


def main():
    """
    Hier werden die Ergebnisse aus der Experiment-Pipeline aggregiert und geplottet.
    Die Ergebnisse aus der Experiment-Pipeline befinden sich in artifacts/evaluation_results.csv.

    Dazu wird das Paket pandas (https://pandas.pydata.org/) verwendet.

    :return:
    """

    # Lese die Ergebnisse aus der Experiment-Pipeline
    data_frame = pandas.read_csv("artifacts/evaluation_results.csv")

    # Festlegung des Output-Pfads der Aggregations-Tabellen
    output_summary_dir = Path("artifacts/summary_tables")
    output_summary_dir.mkdir(parents=True, exist_ok=True)

    # Festlegung des Output-Pfads der Plots
    output_plot_dir = Path("artifacts/plots")
    output_plot_dir.mkdir(parents=True, exist_ok=True)

    # ==============================
    #      Aggregationstabellen
    # ==============================

    # Gruppiere die Daten nach dem Szenario.
    # Pro Szenario soll eine Aggregationstabelle entstehen
    scenarios = data_frame["scenario_name"].unique()
    for scenario in scenarios:
        scenario_dataframe = data_frame[data_frame["scenario_name"] == scenario]

        # Gruppiere innerhalb des Szenarios nach dem Solver
        # Speichere die Mittelwerte von ausgewählten Spalten aus dem Experiment
        aggregated_result = (
            scenario_dataframe
            .groupby("solver_name")
            .agg(
                avg_served=("number_of_requests_served", "mean"),
                avg_unserved=("number_of_requests_unserved", "mean"),
                avg_service_rate=("percentage_of_served_requests", "mean"),
                avg_objective_per_request=("objective_value_per_served_request", "mean"),
                avg_travel_time_per_request=("travel_time_per_served_request", "mean"),
                avg_distance_per_request=("travel_distance_per_served_request", "mean"),
                avg_raw_travel_time_part=("raw_travel_time_part", "mean"),
                avg_raw_travel_cost_part=("raw_travel_cost_part", "mean"),
                avg_raw_capacity_balancing_part=("raw_capacity_balancing_part", "mean"),
                avg_weighted_travel_time_part=("weighted_travel_time_part", "mean"),
                avg_weighted_travel_cost_part=("weighted_travel_cost_part", "mean"),
                avg_weighted_capacity_balancing_part=("weighted_capacity_balancing_part", "mean"),
            )
            .reset_index()
        )

        # Rundung der berechneten Mittelwerte auf zwei Nachkommastellen
        aggregated_result = aggregated_result.round(2)

        # Ausgabe der Aggregationstabelle in der Konsole
        print("\n====================================================")
        print(f"Scenario: {scenario}")
        print("====================================================")
        print(aggregated_result)

        # Speichern der Aggregationstabelle als CSV-Datei
        summary_path = output_summary_dir / f"{scenario}_summary.csv"
        aggregated_result.to_csv(summary_path, index=False)

    # ===============
    #      Plots
    # ===============

    # Plotte pro Solver und Szenario die mittlere Service-Rate aus den Experimenten.
    # Die Service-Rate beschreibt, wie viel Prozent der Anfragen eines Durchlaufs bedient wurden
    service_rate_plot = (
        data_frame.groupby(["scenario_name", "solver_name"])["percentage_of_served_requests"]
        .mean()
        .unstack()
    )

    pyplot.figure()
    service_rate_plot.plot(kind="bar")
    pyplot.ylabel("Service-Rate [%]")
    pyplot.title("Durchschnittliche Service-Rate per Scenario")
    pyplot.tight_layout()
    pyplot.savefig(output_plot_dir / "service_rate_per_scenario.png", dpi=300)
    pyplot.close()

    # Plotte pro Solver und Szenario den mittleren Zielfunktionswert pro bedienter Anfrage aus den Experimenten.
    objective_plot = (
        data_frame.groupby(["scenario_name", "solver_name"])["objective_value_per_served_request"]
        .mean()
        .unstack()
    )

    pyplot.figure()
    objective_plot.plot(kind="bar")
    pyplot.ylabel("Zielfunktionswert pro bedienter Anfrage")
    pyplot.title("Durchschnittlicher Zielfunktionswert pro bedienter Anfrage")
    pyplot.tight_layout()
    pyplot.savefig(output_plot_dir / "objective_per_request.png", dpi=300)
    pyplot.close()

    print("\nAggregationstabellen gespeichert unter:")
    print(output_summary_dir.resolve())

    print("\nPlots gespeichert unter:")
    print(output_plot_dir.resolve())


if __name__ == "__main__":
    main()
