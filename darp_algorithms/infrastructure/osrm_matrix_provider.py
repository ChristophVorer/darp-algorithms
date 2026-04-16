from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

import requests

from darp_algorithms.domain.location import Location

TravelTimeFn = Callable[[Location, Location], timedelta]
TravelDistanceFn = Callable[[Location, Location], float]


class OsrmMatrixValidationException(Exception):
    """
    Diese Exception wird geworfen, wenn ein Fehler bei der Validierung der OsrmMatrix auftritt.

    Dies kann beispielsweise bei Koordinaten entstehen für die OSRM keine Fahrprofil-Daten zur Verfügung stellt. Dies
    kann der Fall sein, wenn eine Koordinate sich im Wasser oder in einem Wald befindet.
    """

    pass


@dataclass(frozen=True)
class MatrixData:
    """
    Struktur, die die Zeit- und Distanzmatrizen umfasst
    """

    time_matrix_seconds: list[list[float]]
    distance_matrix_kilometers: list[list[float]]


class OsrmMatrixProvider:
    """
    Konstruiert aus einer Menge von Locations die notwendige Distanz- und Zeitmatrix für das DARP mithilfe der OSRM-API

    OSRM berechnet dabei die Distanzen und Zeiten nicht für die Luftlinien zwischen den Locations, sondern für die
    schnellsten Fahrtrouten zwischen den Locations abhängig vom Fahrprofil. In unserem Fall ist das Fahrprofil "driving", was
    bedeutet, dass das Fahrprofil für ein Auto angenommen wird.


    Quelle: https://project-osrm.org/docs/v5.24.0/api/#
    """

    def __init__(
            self,
            base_url: str = "https://router.project-osrm.org",
            profile: str = "driving",
            timeout_seconds: int = 30,
    ) -> None:
        """
        :param base_url: Die Base-URL der OSRM-API.
        :param profile: Das Fahrprofil nach dem sich die berechneten Fahrtzeiten und Distanzen richten.
        :param timeout_seconds: Die Zeit nach der ein Timeout-Error geworfen werden soll.
        """

        self.base_url = base_url.rstrip("/")
        self.profile = profile
        self.timeout_seconds = timeout_seconds

    def build_matrices(self, locations: list[Location]) -> MatrixData:
        """
        Baut anhand einer Menge von Locations die entsprechenden Zeit- und Distanzmatrizen und gibt Sie als
        MatrixData-Objekt zurück.
        """

        if not locations:
            raise ValueError("Die Locations-Liste darf nicht leer sein.")

        # Formatierer String für die Anfrage an OSRM, der die Koordinaten der Locations enthält
        coordinates = self._build_coordinate_string(locations)

        # Setzt den String für die Anfrage an die OSRM-API zusammen.
        # Die annotations duration und distance sorgen dafür, dass die Distanz- und Zeitmatrix für alle übergebenen
        # Locations zurückgegeben wird.
        url = (
            f"{self.base_url}/table/v1/{self.profile}/{coordinates}"
            f"?annotations=duration,distance"
        )

        # Senden des Requests + Abfangen von Fehlern bei der Anfrage
        response = requests.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            raise RuntimeError(
                f"OSRM Table Service lieferte keinen erfolgreichen Status: {data}"
            )

        # BOF Validierung der Anfrage-Daten
        duration_matrix = data.get("durations")
        distance_matrix_in_meter = data.get("distances")

        if duration_matrix is None:
            raise RuntimeError("OSRM-Antwort enthält keine 'durations'.")

        if distance_matrix_in_meter is None:
            raise RuntimeError("OSRM-Antwort enthält keine 'distances'.")

        self._validate_square_matrix(duration_matrix)
        self._validate_square_matrix(distance_matrix_in_meter)

        # Die OSRM-API liefert eine Distanz-Matrix in Metern. Da in der restlichen Betrachtung Distanzen in Kilometern
        # betrachtet werden, wird an dieser Stelle von Metern in Kilometern umgerechnet
        distance_matrix_in_kilometers = [
            [float(value) / 1000.0 for value in row]
            for row in distance_matrix_in_meter
        ]

        return MatrixData(
            time_matrix_seconds=duration_matrix,
            distance_matrix_kilometers=distance_matrix_in_kilometers,
        )

    @staticmethod
    def build_travel_time_fn(matrix_data: MatrixData) -> TravelTimeFn:
        """
        Gibt die Time Travel Function für die berechnete Zeitmatrix zurück
        """

        def travel_time(a: Location, b: Location) -> timedelta:
            seconds = matrix_data.time_matrix_seconds[
                a.matrix_node_id
            ][b.matrix_node_id]
            return timedelta(seconds=float(seconds))

        return travel_time

    @staticmethod
    def build_travel_distance_fn(matrix_data: MatrixData) -> TravelDistanceFn:
        """
        Gibt die Travel Distance Function für die berechnete Distanzmatrix zurück.
        Die Distanzen werden in Kilometern zurückgegeben.
        """

        def travel_distance(a: Location, b: Location) -> float:
            return float(
                matrix_data.distance_matrix_kilometers[
                    a.matrix_node_id
                ][b.matrix_node_id]
            )

        return travel_distance

    @staticmethod
    def _build_coordinate_string(locations: list[Location]) -> str:
        """
        Konstruiert aus einer Liste von Locations den Anfrage-String im OSRM-API-Format
        Quelle: https://project-osrm.org/docs/v5.24.0/api/#
        """

        # OSRM erwartet longitude,latitude
        return ";".join(f"{loc.lon},{loc.lat}" for loc in locations)

    @staticmethod
    def _validate_square_matrix(matrix: list[list[float]]) -> None:
        """
        Überprüft, ob die übergebene Matrix quadratisch ist und für jede Position einen Eintrag enthält. Das stellt
        sicher, dass für jede Location-Kombination ein Wert in der jeweiligen Matrix vorhanden ist.
        """

        for row_index, row in enumerate(matrix):
            if len(row) != len(matrix):
                raise RuntimeError("OSRM-Matrix ist nicht quadratisch.")
            for column_index, column_value in enumerate(row):
                if column_value is None:
                    # Der Wert "a7f3c9d2" wird später nur zur Identifizierung der Exception genutzt
                    raise OsrmMatrixValidationException(
                        f"Die OSRM-Matrix enthält einen None-Wert an der Position "
                        f"({row_index},{column_index}). "
                        "Es konnte keine Route für dieses Location-Paar berechnet werden.(a7f3c9d2)"
                    )
