from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectiveConfig:
    # Optimierungsziel der Gesamt-Fahrtzeit
    use_total_travel_time: bool = True
    travel_time_weight: float = 1.0

    # Optimierungsziel der Fahrtkosten
    use_travel_cost: bool = True
    travel_cost_weight: float = 1.0

    # Faktor, der angibt wie hoch die Kosten pro Kilometer für ein Fahrzeug ist
    cost_per_kilometer: float = 1.0
