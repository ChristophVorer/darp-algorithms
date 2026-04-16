from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectiveConfig:
    """
    Definiert die Konfigurationsmöglichkeiten für die Zielfunktion und deren Optimierungsziele
    """

    # ==================================================================================================================
    #    Modellparameter:
    # ==================================================================================================================

    # 'cost_per_kilometer' beschreibt hier den Faktor, der angibt wie hoch die Kosten pro Kilometer für ein Fahrzeug
    # ist. Der Faktor basiert auf realistischen Kostenannahmen für Nutzfahrzeuge, die vom ADACs veröffentlicht
    # wurden. (siehe https://assets.adac.de/Autodatenbank/Autokosten/autokostenuebersicht.pdf)
    cost_per_kilometer: float = 0.8

    # ==================================================================================================================
    #    Optimierungszielsteuerung:
    #    Hier können die einzelnen zu betrachteten Optimierungsziele de- bzw. aktiviert werden.
    # ==================================================================================================================

    # Optimierungsziel - Gesamt-Fahrtzeit
    use_total_travel_time: bool = True

    # Optimierungsziel - Gesamt-Fahrtkosten
    use_travel_cost: bool = True

    # Optimierungsziel - Balancierung der Fahrzeugauslastungen (Imbalance)
    use_capacity_balancing: bool = True

    # ==================================================================================================================
    #    Gewichtungsparameter:
    #    Die Gewichte der Optimierungsziele richten sich nach den Durchschnittswerten der Rohanteile an dem
    #    Zielfunktionswert pro Optimierungsziel. Dazu wurden im ressourcen restriktiven Szenario alle Lösungsverfahren
    #    ohne jegliche Gewichtung auf 20 Durchläufe angewandt und die Rohanteile der Optimierungsziele am
    #    Zielfunktionswert berechnet. Danach wurden die Standard-Gewichte so festgelegt, dass die jeweiligen gewichteten
    #    Anteile der Optimierungsziele am Zielfunktionswert ungefähr in der gleichen Größenordnung liegen.
    # ==================================================================================================================

    # Gewichtungsparameter - Gesamt-Fahrtzeit
    travel_time_weight: float = 1.0

    # Gewichtungsparameter - Gesamt-Fahrtkosten
    travel_cost_weight: float = 110

    # Gewichtungsparameter - Balancierung der Fahrzeugauslastungen (Imbalance)
    capacity_balancing_weight: float = 550000.0
