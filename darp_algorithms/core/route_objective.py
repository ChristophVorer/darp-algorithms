from __future__ import annotations

from .route_state import RouteState
from .objective_config import ObjectiveConfig


def compute_route_objective_function(route_state: RouteState) -> float:
    """
    Berechnet den Zielfunktionswert für einen RouteState.
    Dafür werden die enthaltenen Metriken in RouteState genutzt um mithilfe der übergebenen ObjectiveConfig den
    Zielfunktionswert zu ermitteln

    Returns:
        float:
            Gibt den berechneten Zielfunktionswert für den übergebenen RouteState zurück
    """
    objective_config: ObjectiveConfig = route_state.darp_config.objective_config
    objective_value = 0.0

    if objective_config.use_total_travel_time:
        objective_value += (
            objective_config.travel_time_weight *
            route_state.total_travel_time.total_seconds()
        )

    if objective_config.use_travel_cost:
        objective_value += (
            objective_config.travel_cost_weight *
            objective_config.cost_per_kilometer *
            route_state.total_travel_distance
        )

    return objective_value