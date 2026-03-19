from __future__ import annotations

from .route_state import RouteState
from .objective_config import ObjectiveConfig


def compute_solution_objective_function(
        *,
        route_states: list[RouteState],
        objective_config: ObjectiveConfig,
) -> float:
    objective_value = 0.0

    # Berechnung der Zielfunktionswert-Anteile der routenbasierte Optimierungsziele
    for route_state in route_states:
        # Optimierungsziel - Gesamt-Fahrtzeit
        if objective_config.use_total_travel_time:
            objective_value += (
                    objective_config.travel_time_weight *
                    route_state.total_travel_time.total_seconds()
            )

        # Optimierungsziel - Gesamt-Fahrtkosten
        if objective_config.use_travel_cost:
            objective_value += (
                    objective_config.travel_cost_weight *
                    objective_config.cost_per_kilometer *
                    route_state.total_travel_distance
            )

    # Berechnung der Zielfunktionswert-Anteile der lösungsbasierten Optimierungsziele

    # Optimierungsziel - Balancierung der Fahrzeugauslastung
    if objective_config.use_capacity_balancing:
        imbalance = compute_capacity_imbalance(route_states=route_states)

        # Gewichteter Anteil der Imbalance an der Zielfunktion
        objective_value += (objective_config.capacity_balancing_weight * imbalance)

    return objective_value


def compute_capacity_imbalance(*, route_states: list[RouteState]) -> float:
    # Wenn keine RouteStates übergeben werden, kann kein Imbalance-Wert berechnet werden
    if len(route_states) == 0:
        return 0.0

    # Durchschnittsauslastungen der Routen
    average_loads: list[float] = []

    # Berechnung der Durchschnittsauslastungen
    for route_state in route_states:
        if len(route_state.load) == 0:
            average_load = 0.0
        else:
            average_load = sum(route_state.load) / len(route_state.load)

        average_loads.append(average_load)

    # Durchschnittsauslastung aller Fahrzeuge
    mean_load = sum(average_loads) / len(average_loads)

    # Imbalance der Fahrzeugauslastung:
    # Die Imbalance der Fahrzeugauslastung ist definiert als die mittlere quadratische Abweichung der
    # Durchschnittsauslastung eines Fahrzeugs vom Mittelwert der Durchschnittsauslastungen aller Fahrzeuge
    imbalance = sum(
        (load - mean_load) ** 2 for load in average_loads
    ) / len(average_loads)

    return imbalance
