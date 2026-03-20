from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectiveConfig:
    """
    Definiert die Konfigurationsmöglichkeiten für die Zielfunktion und deren Optimierungsziele

    """
    # ==================================================================================================================
    #    Modellparameter
    #
    # Faktor, der angibt wie hoch die Kosten pro Kilometer für ein Fahrzeug ist.
    # Der Faktor basiert auf realistischen Kostenannahmen für Nutzfahrzeuge, die vom ADACs veröffentlicht wurden.
    # (https://assets.adac.de/Autodatenbank/Autokosten/autokostenuebersicht.pdf)
    # ==================================================================================================================
    cost_per_kilometer: float = 0.8

    # ==================================================================================================================
    #    Optimierungszielsteuerung
    # ==================================================================================================================

    # Optimierungsziel der Gesamt-Fahrtzeit
    use_total_travel_time: bool = True

    # Optimierungsziel der Gesamt-Fahrtkosten
    use_travel_cost: bool = True

    # Optimierungsziel der Balancierung der Fahrzeugauslastungen (Imbalance)
    use_capacity_balancing: bool = True

    # ==================================================================================================================
    #    Gewichtungsparameter:
    #    Die Gewichte der Optimierungsziele richten sich nach den Durchschnittswerten der Rohanteile an dem
    #    Zielfunktionswert pro Optimierungsziel. Dazu wurden im ressourcen restriktiven Szenario alle Lösungsverfahren
    #    ohne jegliche Gewichtung auf 20 Durchläufe angewandt und die Rohanteile der Optimierungsziele am Zielfunktionswert
    #    berechnet. Danach wurden die Standard-Gewichte so festgelegt, dass die jeweiligen gewichteten Anteile der
    #    Optimierungsziele am Zielfunktionswert ungefähr in der gleichen Größenordnung liegen.
    # ==================================================================================================================

    # Gewichtungsparameter der Gesamt-Fahrtzeit
    travel_time_weight: float = 1.0

    # Gewichtungsparameter der Gesamt-Fahrtkosten
    travel_cost_weight: float = 110

    # Gewichtungsparameter der Balancierung der Fahrzeugauslastungen (Imbalance)
    capacity_balancing_weight: float = 220000.0
