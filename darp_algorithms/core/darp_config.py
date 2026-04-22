from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from .objective_config import ObjectiveConfig
from .constraint_config import ConstraintConfig


@dataclass(frozen=True)
class DarpConfig:
    """
    Definiert das zugrunde liegenden DARP. Dazu werden die Ausprägungen der Design-Parameter wie Service-Zeit pro Stopp
    oder maximale Fahrzeugkapazität sowie die Konfiguration der Zielfunktion und der Nebenbedingungen definiert
    """

    # ==================================================================================================================
    #    DARP Design-Parameter
    # ==================================================================================================================

    # Kapazität der Fahrzeuge
    vehicle_capacity: int

    # Service-Zeit pro Stopp
    service_duration: timedelta = timedelta(seconds=0)

    # Puffer des gewünschten Abholzeitpunkts
    # Obere Grenze des Zeitfensters ergibt sich aus "Gewünschter Abholzeitpunkt + Abholpuffer"
    pickup_buffer: timedelta = timedelta(minutes=5)

    # ==================================================================================================================
    #    DARP Konfigurations-Parameter
    # ==================================================================================================================

    # Konfiguration der Zielfunktion:
    # Enthält die Informationen über die Zusammensetzung und Gewichtungen der Optimierungsziele der Zielfunktion.
    objective_config: ObjectiveConfig = field(default_factory=ObjectiveConfig)

    # Konfiguration der Nebenbedingungen:
    # Enthält die Informationen über die enthaltenen Nebenbedingungen und deren Ausprägungen
    constraint_config: ConstraintConfig = field(default_factory=ConstraintConfig)
