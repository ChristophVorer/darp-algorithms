from __future__ import annotations

from dataclasses import dataclass

from darp_algorithms.core import DarpConfig, DarpInstance
from darp_algorithms.domain.location import Location
from darp_algorithms.domain.request import Request
from darp_algorithms.domain.vehicle import Vehicle
from .osrm_matrix_provider import OsrmMatrixProvider


@dataclass
class DarpInstanceGenerator:
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

        """
        Remapping der aktuellen Locations
        """
        ordered_locations, remapped_vehicles, remapped_requests = self.remap_locations_for_matrix(
            vehicles=vehicles,
            requests=requests,
        )

        """
        Berechnung der Distanz- und Zeitmatrix
        """
        matrix_data = self.osrm_matrix_provider.build_matrices(ordered_locations)

        """
        Definition der Time Travel Function und Travel Distance Function
        """
        travel_time = self.osrm_matrix_provider.build_travel_time_fn(matrix_data)
        travel_distance = self.osrm_matrix_provider.build_travel_distance_fn(matrix_data)

        """
        Definiert das Request Dictionary und die Request Order
        """
        request_dict = {request.id: request for request in remapped_requests}
        request_order = [request.id for request in remapped_requests]

        """
        Gebe die vollständige Darp-Instanz zurück
        """
        return DarpInstance(
            darp_config=darp_config,
            vehicles=remapped_vehicles,
            requests=request_dict,
            request_order=request_order,
            travel_time=travel_time,
            travel_distance=travel_distance,
        )

    @staticmethod
    def remap_locations_for_matrix(
            *,
            vehicles: list[Vehicle],
            requests: list[Request],
    ) -> tuple[list[Location], list[Vehicle], list[Request]]:
        """
        1. Sammelt alle Locations der Anfragen und vergibt ihnen konsistente matrix_node_id-Werte.
        2. Erzeugt darauf basierend neue Vehicle- und Request-Objekte mit konsistenten matrix_node_id

        Die "matrix_node_id" steht später für die Position einer Location in der jeweiligen Distanz- bzw. Zeitmatrix, die aus
        OSRM gewonnen wird.

        Returns:
            tuple[list[Location], list[Vehicle], list[Request]]:
                - Geordnete Liste aller Locations mit konsistenten matrix_node_ids
                - Vehicles mit neu gemappten Startpositionen
                - Requests mit neu gemappten Pickup-/Delivery-Locations
        """

        """
        Mapping von "alter" Location zu "neuer" Location mit konsistenter matrix_node_id.
        Hierbei werden Koordinaten anstatt Location-Objekte betrachtet, dies verhindert, dass Routen für Locations mit 
        gleichen Koordinaten aber unterschiedlicher Id, doppelt durch OSRM berechnet werden
        """
        coordinate_to_new_location: dict[tuple[float, float], Location] = {}
        # Geordnete Liste der Locations
        ordered_locations: list[Location] = []

        def get_or_create_remapped_location(old_location: Location) -> Location:
            """
            Erstellt aus einer Location eine neue Location mit konsistenter matrix_node_id.
            Wurde bereits eine neue Location angelegt, wird stattdessen die neu angelegte Location zurückgegeben
            :param old_location:
            :return:
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

        # Neu-Zuordnung der Locations für die Startpositionen der Fahrzeuge
        remapped_vehicles: list[Vehicle] = []
        for vehicle in vehicles:
            remapped_vehicle = Vehicle(
                start_position=get_or_create_remapped_location(vehicle.start_position),
                start_time=vehicle.start_time,
                id=vehicle.id,
            )
            remapped_vehicles.append(remapped_vehicle)

        # Neu-Zuordnung der Anfragen für die Startpositionen der Fahrzeuge
        remapped_requests: list[Request] = []
        for request in requests:
            remapped_request = Request(
                pickup=get_or_create_remapped_location(request.pickup),
                delivery=get_or_create_remapped_location(request.delivery),
                passengers=request.passengers,
                desired_pickup_time=request.desired_pickup_time,
                id=request.id,
            )
            remapped_requests.append(remapped_request)

        return ordered_locations, remapped_vehicles, remapped_requests
