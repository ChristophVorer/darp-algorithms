import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def main():
    df = pd.read_csv("artifacts/evaluation_results.csv")

    output_summary_dir = Path("artifacts/summary_tables")
    output_summary_dir.mkdir(parents=True, exist_ok=True)

    output_plot_dir = Path("artifacts/plots")
    output_plot_dir.mkdir(parents=True, exist_ok=True)

    scenarios = df["scenario_name"].unique()

    for scenario in scenarios:
        scenario_df = df[df["scenario_name"] == scenario]

        summary = (
            scenario_df
            .groupby("solver_name")
            .agg(
                avg_served=("number_of_requests_served", "mean"),
                avg_unserved=("number_of_requests_unserved", "mean"),
                avg_service_rate=("percentage_of_served_requests", "mean"),
                avg_objective_per_request=("objective_value_per_served_request", "mean"),
                avg_travel_time_per_request=("travel_time_per_served_request", "mean"),
                avg_distance_per_request=("travel_distance_per_served_request", "mean"),
            )
            .reset_index()
        )

        summary = summary.round(2)

        print("\n====================================================")
        print(f"Scenario: {scenario}")
        print("====================================================")
        print(summary)

        # CSV speichern
        summary_path = output_summary_dir / f"{scenario}_summary.csv"
        summary.to_csv(summary_path, index=False)

    # -----------------------------
    # Plot: Service Rate
    # -----------------------------

    service_rate_plot = (
        df.groupby(["scenario_name", "solver_name"])["percentage_of_served_requests"]
        .mean()
        .unstack()
    )

    plt.figure()
    service_rate_plot.plot(kind="bar")
    plt.ylabel("Service Rate [%]")
    plt.title("Average Service Rate per Scenario")
    plt.tight_layout()
    plt.savefig(output_plot_dir / "service_rate_per_scenario.png", dpi=300)
    plt.close()

    # -----------------------------
    # Plot: Objective per Request
    # -----------------------------

    objective_plot = (
        df.groupby(["scenario_name", "solver_name"])["objective_value_per_served_request"]
        .mean()
        .unstack()
    )

    plt.figure()
    objective_plot.plot(kind="bar")
    plt.ylabel("Objective Value per Served Request")
    plt.title("Average Objective per Served Request")
    plt.tight_layout()
    plt.savefig(output_plot_dir / "objective_per_request.png", dpi=300)
    plt.close()

    print("\nSummary CSV files gespeichert unter:")
    print(output_summary_dir.resolve())

    print("\nPlots gespeichert unter:")
    print(output_plot_dir.resolve())


if __name__ == "__main__":
    main()
