from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ScenarioConfig:
    """
    Konfiguration zur Synthese einer DARP-Instanz.
    """

    # Random-Seed für die randomisierte Generierung der Anfragen
    random_seed: int

    # Anzahl der Anfragen
    number_of_requests: int

    # Anzahl der Fahrzeuge
    number_of_vehicles: int

    # Startzeit des Szenarios
    scenario_start_time: datetime

    # Endzeit des Szenarios
    scenario_end_time: datetime

    # Minimale Anzahl der Passagiere pro Anfrage
    min_passengers: int = 1

    # Maximale Anzahl der Passagiere pro Anfrage
    max_passengers: int = 3

    """
    Bounding-Box, die den Wertebereich der Koordinaten der Abhol-und Zielort der Anfragen definiert.
    
    Die Standardwerte bilden eine Bounding-Box um Münster ca. 5 km um die Innenstadt herum.
    """
    min_lat: float = 51.9116
    max_lat: float = 52.0016
    min_lon: float = 7.5651
    max_lon: float = 7.7103

    """
    Koordinaten-Paar, welches den Standort des Depots beschreibt.
    """
    depot_location_lat: float = 51.9566
    depot_location_lon: float = 7.6377

    """
    Die minimale und maximale Luftlinien-Distanz von Abhol- und Zielort innerhalb einer Anfrage
    """
    min_direct_distance_km: float = 1.0
    max_direct_distance_km: float = 5.0
