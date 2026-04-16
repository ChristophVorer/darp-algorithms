import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DESIRED_SCENARIO_ORDER = ["basic", "time_restrictive", "resource_restrictive"]

SCENARIO_MAPPING = {
    "basic": "Basis-Szenario",
    "time_restrictive": "Zeitlich restriktives Szenario",
    "resource_restrictive": "Ressourcen-restriktives Szenario",
}

SOLVER_ORDER = ["greedy_baseline", "greedy_refined", "local_search"]

SOLVER_MAPPING_PLOT = {
    "greedy_baseline": "Greedy\nBaseline",
    "greedy_refined": "Greedy\nRefined",
    "local_search": "Local Search",
}

SOLVER_MAPPING_TABLE = {
    "greedy_baseline": "Greedy Baseline",
    "greedy_refined": "Greedy Refined",
    "local_search": "Local Search",
}

COMPONENT_COLORS = {
    "travel_time": "tab:blue",
    "travel_cost": "tab:orange",
    "capacity": "tab:green",
}


def create_output_directories() -> tuple[Path, Path]:
    """
    Erstellt die Output-Paths für die Zusammenfassungstabellen
    """
    output_summary_dir = Path("artifacts/summary_tables")
    output_summary_dir.mkdir(parents=True, exist_ok=True)

    output_plot_dir = Path("artifacts/plots")
    output_plot_dir.mkdir(parents=True, exist_ok=True)

    return output_summary_dir, output_plot_dir


def aggregate_scenario_results(scenario_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregiert die Evaluationsmetriken innerhalb des DataFrame-Objekts und gibt es zurück.
    """
    aggregated = (
        scenario_dataframe
        .groupby("solver_name", as_index=False)
        .agg(
            avg_served=("number_of_requests_served", "mean"),
            std_served=("number_of_requests_served", "std"),
            avg_unserved=("number_of_requests_unserved", "mean"),
            std_unserved=("number_of_requests_unserved", "std"),
            avg_service_rate=("percentage_of_served_requests", "mean"),
            std_service_rate=("percentage_of_served_requests", "std"),
            avg_total_objective_value=("total_objective_value", "mean"),
            std_total_objective_value=("total_objective_value", "std"),
            avg_objective_per_request=("objective_value_per_served_request", "mean"),
            std_objective_per_request=("objective_value_per_served_request", "std"),
            avg_travel_time_per_request=("travel_time_per_served_request", "mean"),
            std_travel_time_per_request=("travel_time_per_served_request", "std"),
            avg_distance_per_request=("travel_distance_per_served_request", "mean"),
            std_distance_per_request=("travel_distance_per_served_request", "std"),
            avg_weighted_travel_time_part=("weighted_travel_time_part", "mean"),
            std_weighted_travel_time_part=("weighted_travel_time_part", "std"),
            avg_weighted_travel_cost_part=("weighted_travel_cost_part", "mean"),
            std_weighted_travel_cost_part=("weighted_travel_cost_part", "std"),
            avg_weighted_capacity_balancing_part=("weighted_capacity_balancing_part", "mean"),
            std_weighted_capacity_balancing_part=("weighted_capacity_balancing_part", "std"),
        )
    )

    aggregated["solver_name"] = pd.Categorical(
        aggregated["solver_name"],
        categories=SOLVER_ORDER,
        ordered=True,
    )
    aggregated = aggregated.sort_values("solver_name").reset_index(drop=True)
    return aggregated


def format_mean_std(mean_value: float, std_value: float, decimals: int = 2) -> str:
    """
    Formatiert den Mittelwert sowie die Standardabweichung als String
    """

    return f"{{{mean_value:.{decimals}f} (+- {std_value:.{decimals}f})}}"


def format_absolute_and_percentage(
        value: float,
        total: float,
        decimals_value: int = 2,
        decimals_pct: int = 1,
) -> str:
    """
    Berechnet den relativen Anteil eines Werts am übergebenen Gesamtwert und formatiert diese Werte als String.
    """

    if pd.isna(total) or total == 0:
        percentage = 0.0
    else:
        percentage = 100.0 * value / total

    return f"{{{value:.{decimals_value}f} ({percentage:.{decimals_pct}f}\\%)}}"


def map_solver_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Mappt die technischen Namen der Solver auf sprechende Namen aus dem `SOLVER_MAPPING_TABLE`
    """

    df = dataframe.copy()
    df["solver_name"] = df["solver_name"].astype(str).map(
        lambda x: SOLVER_MAPPING_TABLE.get(x, x)
    )
    return df


def compute_component_percentages(
        travel_time: float,
        travel_cost: float,
        capacity: float,
        include_capacity: bool,
) -> tuple[float, float, float]:
    """
    Berechnet die relativen Anteile der Zielfunktionskomponenten am Gesamtzielfunktionswert
    """

    if include_capacity:
        total = travel_time + travel_cost + capacity
        if total == 0:
            return 0.0, 0.0, 0.0
        return (
            100.0 * travel_time / total,
            100.0 * travel_cost / total,
            100.0 * capacity / total,
        )

    total = travel_time + travel_cost
    if total == 0:
        return 0.0, 0.0, 0.0

    return (
        100.0 * travel_time / total,
        100.0 * travel_cost / total,
        0.0,
    )


def build_main_metrics_table(aggregated_result: pd.DataFrame) -> pd.DataFrame:
    """
    Baut das Dataframe für die Hauptmetriken des Experiments zusammen.

    Die Hauptmetriken bestehen aus der Service-Rate sowie dem Zielfunktionswert pro bedienter Anfrage
    """

    df = map_solver_names(aggregated_result)

    return pd.DataFrame({
        "solver": df["solver_name"],
        "service_rate": [
            format_mean_std(mean, std)
            for mean, std in zip(df["avg_service_rate"], df["std_service_rate"])
        ],
        "objective_per_request": [
            format_mean_std(mean, std)
            for mean, std in zip(df["avg_objective_per_request"], df["std_objective_per_request"])
        ],
    })


def build_efficiency_table(aggregated_result: pd.DataFrame) -> pd.DataFrame:
    """
    Baut das Dataframe für die Effizienzmetriken des Experiments zusammen.

    Die Effizienzmetriken bestehen aus der Fahrtzeit und Fahrtdistanz pro Anfrage
    """

    df = map_solver_names(aggregated_result)

    return pd.DataFrame({
        "solver": df["solver_name"],
        "travel_time_per_request": [
            format_mean_std(mean, std)
            for mean, std in zip(df["avg_travel_time_per_request"], df["std_travel_time_per_request"])
        ],
        "distance_per_request": [
            format_mean_std(mean, std)
            for mean, std in zip(df["avg_distance_per_request"], df["std_distance_per_request"])
        ],
    })


def build_combined_objective_breakdown_table(data_frame: pd.DataFrame) -> pd.DataFrame:
    """
    Baut für die unterschiedlichen Szenarien und Ergebnisse aus dem Experiment ein Dataframe, welches die
    Zusammensetzung der Zielfunktion wiedergibt.

    Dazu werden die absoluten Werte der gewichteten Zielfunktionskomponenten sowie deren relativer Anteil am
    Gesamtzielfunktionswert bestimmt und in das Dataframe integriert.
    """

    rows = []

    for scenario in DESIRED_SCENARIO_ORDER:
        scenario_dataframe = data_frame[data_frame["scenario_name"] == scenario]

        if scenario_dataframe.empty:
            continue

        aggregated_result = aggregate_scenario_results(scenario_dataframe)
        aggregated_result = map_solver_names(aggregated_result)

        for _, row in aggregated_result.iterrows():
            solver_name = row["solver_name"]

            weighted_travel_time = float(row["avg_weighted_travel_time_part"])
            weighted_travel_cost = float(row["avg_weighted_travel_cost_part"])
            weighted_capacity = float(row["avg_weighted_capacity_balancing_part"])

            include_capacity = scenario == "resource_restrictive"

            travel_time_pct, travel_cost_pct, capacity_pct = compute_component_percentages(
                travel_time=weighted_travel_time,
                travel_cost=weighted_travel_cost,
                capacity=weighted_capacity,
                include_capacity=include_capacity,
            )

            rows.append({
                "scenario": SCENARIO_MAPPING.get(scenario, scenario),
                "solver": solver_name,
                "weighted_travel_time_pct": f"{{{travel_time_pct:.1f}\\%}}",
                "weighted_travel_cost_pct": f"{{{travel_cost_pct:.1f}\\%}}",
                "weighted_capacity_pct": f"{{{capacity_pct:.1f}\\%}}" if include_capacity else "{--}",
            })

    return pd.DataFrame(rows)


def save_combined_objective_breakdown_table_as_csv(
        data_frame: pd.DataFrame,
        output_summary_dir: Path,
) -> None:
    """
    Speichere die Tabelle für die Zusammensetzung der Zielfunktion als CSV-Datei
    """

    combined_objective_table = build_combined_objective_breakdown_table(data_frame)
    output_path = output_summary_dir / "combined_objective_breakdown.csv"
    combined_objective_table.to_csv(output_path, index=False)

    print("\n====================================================")
    print("Kombinierte Zielfunktionszerlegung")
    print("====================================================")
    print(combined_objective_table.to_string(index=False))


def save_combined_objective_breakdown_as_latex(
        data_frame: pd.DataFrame,
        output_summary_dir: Path,
) -> None:
    """
    Speichere die Tabelle für die Zusammensetzung der Zielfunktion als Latex-Datei
    """

    combined_table = build_combined_objective_breakdown_table(data_frame)

    scenario_order_labels = [
        SCENARIO_MAPPING["basic"],
        SCENARIO_MAPPING["time_restrictive"],
        SCENARIO_MAPPING["resource_restrictive"],
    ]

    output_path = output_summary_dir / "combined_objective_breakdown_table.tex"

    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Relative Zusammensetzung der Zielfunktion über alle Szenarien und Lösungsverfahren}",
        r"\label{tab:combined_objective_breakdown}",
        r"\begin{tabular}{llll}",
        r"\toprule",
        r"Lösungsverfahren & Fahrtzeit (\%) & Fahrtkosten (\%) & Auslastung (\%) \\",
        r"\midrule"
    ]

    for scenario_index, scenario_label in enumerate(scenario_order_labels):
        scenario_df = combined_table[combined_table["scenario"] == scenario_label]

        if scenario_df.empty:
            continue

        lines.append(rf"\multicolumn{{4}}{{l}}{{\textbf{{{scenario_label}}}}} \\")

        for _, row in scenario_df.iterrows():
            solver = row["solver"]
            travel_time = str(row["weighted_travel_time_pct"]).replace("{", "").replace("}", "")
            travel_cost = str(row["weighted_travel_cost_pct"]).replace("{", "").replace("}", "")
            capacity = str(row["weighted_capacity_pct"]).replace("{", "").replace("}", "")

            lines.append(
                rf"{solver} & {travel_time} & {travel_cost} & {capacity} \\"
            )

        if scenario_index < len(scenario_order_labels) - 1:
            lines.append(r"\midrule")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n====================================================")
    print("LaTeX-Tabelle für kombinierte Zielfunktionszerlegung gespeichert")
    print("====================================================")
    print(output_path.resolve())


def save_summary_tables_for_scenario(
        aggregated_result: pd.DataFrame,
        output_summary_dir: Path,
        scenario: str,
) -> None:
    """
    Bildet die Tabellen für die Haupt- und Effizienzmetriken
    """

    rounded_result = aggregated_result.round(2)

    main_metrics_table = build_main_metrics_table(rounded_result)
    efficiency_table = build_efficiency_table(rounded_result)

    main_metrics_table.to_csv(output_summary_dir / f"{scenario}_main_metrics.csv", index=False)
    efficiency_table.to_csv(output_summary_dir / f"{scenario}_efficiency_metrics.csv", index=False)

    print("\n====================================================")
    print(f"Szenario: {scenario}")
    print("====================================================")
    print("\nHauptmetriken")
    print(main_metrics_table.to_string(index=False))
    print("\nEffizienzmetriken")
    print(efficiency_table.to_string(index=False))


def generate_summary_tables(data_frame: pd.DataFrame, output_summary_dir: Path) -> None:
    """
    Generiert für alle Szenarien die entsprechenden Dataframes und speichert Tabellen für die Haupt- und
    Effizienzmetriken.
    """

    for scenario in DESIRED_SCENARIO_ORDER:
        scenario_dataframe = data_frame[data_frame["scenario_name"] == scenario]

        if scenario_dataframe.empty:
            continue

        aggregated_result = aggregate_scenario_results(scenario_dataframe)
        save_summary_tables_for_scenario(aggregated_result, output_summary_dir, scenario)


def collect_boxplot_data(
        scenario_dataframe: pd.DataFrame,
        value_column: str,
) -> tuple[list[pd.Series], list[str]]:
    """
    Sammelt die Daten einer Evaluationsmetrik für einen Boxplot
    """

    data = []
    labels = []

    for solver in SOLVER_ORDER:
        subset = scenario_dataframe[scenario_dataframe["solver_name"] == solver][value_column]

        if not subset.empty:
            data.append(subset)
            labels.append(SOLVER_MAPPING_PLOT.get(solver, solver))

    return data, labels


def create_boxplot(
        data: list[pd.Series],
        labels: list[str],
        title: str,
        output_path: Path,
        y_limits: tuple[float, float] | None = None,
) -> None:
    """
    Erstellt einen Boxplot anhand der übergebenen Parameter
    """

    figure, axes = plt.subplots(figsize=(10, 6))

    axes.boxplot(data)
    axes.set_xticklabels(labels, rotation=0)
    axes.set_title(title)
    axes.grid(axis="y", linestyle="--", alpha=0.5)

    if y_limits is not None:
        axes.set_ylim(*y_limits)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def generate_boxplots(data_frame: pd.DataFrame, output_plot_dir: Path) -> None:
    """
    Generiert pro Szenario die Boxplots für die Service-Rate und dem Zielfunktionswert jedes Solvers
    """

    for scenario in DESIRED_SCENARIO_ORDER:
        scenario_dataframe = data_frame[data_frame["scenario_name"] == scenario]

        if scenario_dataframe.empty:
            continue

        scenario_label = SCENARIO_MAPPING.get(scenario, scenario)

        service_rate_data, service_rate_labels = collect_boxplot_data(
            scenario_dataframe,
            "percentage_of_served_requests",
        )
        create_boxplot(
            data=service_rate_data,
            labels=service_rate_labels,
            title=f"Verteilung der Service-Rate – {scenario_label}",
            output_path=output_plot_dir / f"{scenario}_service_rate_boxplot.png",
            y_limits=(0, 100),
        )

        objective_data, objective_labels = collect_boxplot_data(
            scenario_dataframe,
            "objective_value_per_served_request",
        )
        create_boxplot(
            data=objective_data,
            labels=objective_labels,
            title=f"Verteilung des Zielfunktionswerts pro bedienter Anfrage – {scenario_label}",
            output_path=output_plot_dir / f"{scenario}_objective_per_request_boxplot.png",
        )


def build_component_plot_data(data_frame: pd.DataFrame) -> pd.DataFrame:
    """
    Stellt die Daten für den Plot über die Zusammensetzung des Zielfunktionswerts zusammen
    """

    rows = []

    for scenario in DESIRED_SCENARIO_ORDER:
        scenario_dataframe = data_frame[data_frame["scenario_name"] == scenario]
        if scenario_dataframe.empty:
            continue

        aggregated_result = aggregate_scenario_results(scenario_dataframe)

        for _, row in aggregated_result.iterrows():
            rows.append({
                "scenario_name": scenario,
                "solver_name": row["solver_name"],
                "avg_total_objective_value": row["avg_total_objective_value"],
                "avg_weighted_travel_time_part": row["avg_weighted_travel_time_part"],
                "avg_weighted_travel_cost_part": row["avg_weighted_travel_cost_part"],
                "avg_weighted_capacity_balancing_part": row["avg_weighted_capacity_balancing_part"],
            })

    result = pd.DataFrame(rows)
    if not result.empty:
        result["solver_name"] = pd.Categorical(
            result["solver_name"],
            categories=SOLVER_ORDER,
            ordered=True,
        )
        result = result.sort_values(["scenario_name", "solver_name"]).reset_index(drop=True)

    return result


def generate_objective_component_plot(data_frame: pd.DataFrame, output_plot_dir: Path) -> None:
    """
    Generiert für das ressourcen-restriktive Szenario das gestapelte Balkendiagramm über Zusammensetzung des
    Zielfunktionswerts.
    """

    component_plot = build_component_plot_data(data_frame)

    if component_plot.empty:
        return

    scenario = "resource_restrictive"
    scenario_dataframe = component_plot[component_plot["scenario_name"] == scenario]

    if scenario_dataframe.empty:
        return

    figure, axes = plt.subplots(figsize=(8, 6))

    bar_width = 0.6
    x_positions = []
    x_labels = []

    show_travel_time_label = True
    show_travel_cost_label = True
    show_capacity_label = True

    for i, solver in enumerate(SOLVER_ORDER):
        solver_dataframe = scenario_dataframe[scenario_dataframe["solver_name"] == solver]
        if solver_dataframe.empty:
            continue

        row = solver_dataframe.iloc[0]

        travel_time = float(row["avg_weighted_travel_time_part"])
        travel_cost = float(row["avg_weighted_travel_cost_part"])
        capacity = float(row["avg_weighted_capacity_balancing_part"])

        travel_time_percentage, travel_cost_percentage, capacity_percentage = compute_component_percentages(
            travel_time=travel_time,
            travel_cost=travel_cost,
            capacity=capacity,
            include_capacity=True,
        )

        axes.bar(
            i,
            travel_time_percentage,
            width=bar_width,
            color=COMPONENT_COLORS["travel_time"],
            label="Gewichtete Fahrtzeit" if show_travel_time_label else "",
        )
        show_travel_time_label = False

        axes.bar(
            i,
            travel_cost_percentage,
            width=bar_width,
            bottom=travel_time_percentage,
            color=COMPONENT_COLORS["travel_cost"],
            label="Gewichtete Fahrtkosten" if show_travel_cost_label else "",
        )
        show_travel_cost_label = False

        axes.bar(
            i,
            capacity_percentage,
            width=bar_width,
            bottom=travel_time_percentage + travel_cost_percentage,
            color=COMPONENT_COLORS["capacity"],
            label="Gewichtete Auslastung" if show_capacity_label else "",
        )
        show_capacity_label = False

        x_positions.append(i)
        x_labels.append(SOLVER_MAPPING_PLOT.get(solver, solver))

    axes.set_xticks(x_positions)
    axes.set_xticklabels(x_labels)
    axes.set_title(
        "Relative Zusammensetzung der Zielfunktion im ressourcen-restriktiven Szenario",
        pad=30
    )
    axes.set_ylabel("Anteil (%)")
    axes.set_ylim(0, 105)
    axes.set_yticks(np.arange(0, 101, 10))
    axes.grid(axis="y", linestyle="--", alpha=0.5)

    axes.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=3)

    plt.tight_layout()
    plt.savefig(output_plot_dir / "objective_components_resource_only.png", dpi=300)
    plt.close()


def main() -> None:
    """
    Erstellt die gesamten Zusammenfassungstabellen und Plots für die Ergebnisse in `artifacts/evaluation_results.csv`
    """

    data_frame = pd.read_csv("artifacts/evaluation_results.csv")
    output_summary_dir, output_plot_dir = create_output_directories()

    generate_summary_tables(data_frame, output_summary_dir)
    save_combined_objective_breakdown_table_as_csv(data_frame, output_summary_dir)
    save_combined_objective_breakdown_as_latex(data_frame, output_summary_dir)
    generate_boxplots(data_frame, output_plot_dir)
    generate_objective_component_plot(data_frame, output_plot_dir)

    print("\nTabellen gespeichert unter:")
    print(output_summary_dir.resolve())

    print("\nPlots gespeichert unter:")
    print(output_plot_dir.resolve())


if __name__ == "__main__":
    main()
