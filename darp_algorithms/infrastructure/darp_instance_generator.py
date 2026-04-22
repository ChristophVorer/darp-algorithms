from __future__ import annotations

from dataclasses import dataclass

from darp_algorithms.core import DarpConfig, DarpInstance
from darp_algorithms.domain.location import Location
from darp_algorithms.domain.request import Request
from darp_algorithms.domain.vehicle import Vehicle
from .osrm_matrix_provider import OsrmMatrixProvider


@dataclass
class DarpInstanceGenerator:
    """
    Klasse die für die Erstellung und Generierung einer DarpInstanz verantwortlich ist.

    Sie nutzt dazu den `OsrmMatrixProvider`, welcher über OSRM-API die Zeit- und Distanzmatrizen bestimmt.
    """

    osrm_matrix_provider: OsrmMatrixProvider

    def generate_instance(
            self,
            *,
            darp_config: DarpConfig,
            vehicles: list[Vehicle],
            requests: list[Request],
    ) -> DarpInstance:
        """
        Generiert aus einer DARP-Konfiguration, einer Menge von Fahrzeuge und einer Menge von Anfragen eine vollständige
        DARP-Instanz
        """

        # Remapping der aktuellen Locations:
        # Sorgt dafür, dass allen Requests und deren Locations sowie allen Fahrzeuge konsistente UUIDs innerhalb der
        # Matrizen zugewiesen werden.
        ordered_locations, remapped_vehicles, remapped_requests = self.remap_locations_for_matrix(
            vehicles=vehicles,
            requests=requests,
        )

        # Berechnung der Distanz- und Zeitmatrix über den OsrmMatrixProvider
        matrix_data = self.osrm_matrix_provider.build_matrices(ordered_locations)

        # Definition der Time Travel Function und Travel Distance Function über die generierte Distanz- und Zeitmatrix
        travel_time = self.osrm_matrix_provider.build_travel_time_fn(matrix_data)
        travel_distance = self.osrm_matrix_provider.build_travel_distance_fn(matrix_data)

        request_dict = {request.id: request for request in remapped_requests}
        request_order = [request.id for request in remapped_requests]

        return DarpInstance(
            darp_config=darp_config,
            vehicles=remapped_vehicles,
            requests=request_dict,
            request_order=request_order,
            travel_time=travel_time,
            travel_distance=travel_distance,
        )

    @staticmethod
    def _get_or_create_remapped_location(
            *,
            old_location: Location,
            coordinate_to_new_location: dict[tuple[float, float], Location],
            ordered_locations: list[Location],
    ) -> Location:
        """
        Weist einer Location eine neue konsistente `matrix_node_id` zu, sofern nicht bereits eine Location mit denselben
        Koordinaten vorhanden ist.

        Locations mit identischen Koordinaten werden auf dieselben Locations abgebildet, damit sie in der Zeit- und
        Distanzmatrix nicht doppelt berechnet werden.
        """

        key = (old_location.lat, old_location.lon)

        if key in coordinate_to_new_location:
            return coordinate_to_new_location[key]

        new_location = Location(
            lat=old_location.lat,
            lon=old_location.lon,
            matrix_node_id=len(ordered_locations),
        )
        coordinate_to_new_location[key] = new_location
        ordered_locations.append(new_location)
        return new_location

    @staticmethod
    def remap_locations_for_matrix(
            *,
            vehicles: list[Vehicle],
            requests: list[Request],
    ) -> tuple[list[Location], list[Vehicle], list[Request]]:
        """
        1. Vergibt für alle Locations der Anfragen konsistente matrix_node_id-Werte.
        2. Erzeugt auf Basis der neuen matrix_node_ids neue Vehicle- und Request-Objekte mit konsistenten ids.

        Die "matrix_node_id" steht später für die Position einer Location in der jeweiligen Distanz- bzw. Zeitmatrix,
        die aus dem OsrmMatrixProvider gewonnen wird.

        Gibt ein Tupel zurück, bestehend aus:
                - Geordnete Liste aller Locations mit konsistenten matrix_node_ids (list[Location])
                - Vehicles mit neu gemappten Startpositionen (list[Vehicle])
                - Requests mit neu gemappten Pickup-/Delivery-Locations (list[Request])
        """

        # Mapping von "alter" Location zu "neuer" Location mit konsistenter matrix_node_id.
        coordinate_to_new_location: dict[tuple[float, float], Location] = {}
        # Geordnete Liste der Locations
        ordered_locations: list[Location] = []

        # Neu-Zuordnung der Locations für die Startpositionen der Fahrzeuge
        remapped_vehicles: list[Vehicle] = []
        for vehicle in vehicles:
            remapped_vehicle = Vehicle(
                start_position=DarpInstanceGenerator._get_or_create_remapped_location(
                    old_location=vehicle.start_position,
                    coordinate_to_new_location=coordinate_to_new_location,
                    ordered_locations=ordered_locations,
                ),
                start_time=vehicle.start_time,
                id=vehicle.id,
            )
            remapped_vehicles.append(remapped_vehicle)

        # Neu-Zuordnung der Anfragen für die Startpositionen der Fahrzeuge
        remapped_requests: list[Request] = []
        for request in requests:
            pickup = DarpInstanceGenerator._get_or_create_remapped_location(
                old_location=request.pickup,
                coordinate_to_new_location=coordinate_to_new_location,
                ordered_locations=ordered_locations,
            )
            delivery = DarpInstanceGenerator._get_or_create_remapped_location(
                old_location=request.delivery,
                coordinate_to_new_location=coordinate_to_new_location,
                ordered_locations=ordered_locations,
            )

            remapped_request = Request(
                pickup=pickup,
                delivery=delivery,
                passengers=request.passengers,
                desired_pickup_time=request.desired_pickup_time,
                id=request.id,
            )
            remapped_requests.append(remapped_request)

        return ordered_locations, remapped_vehicles, remapped_requests
