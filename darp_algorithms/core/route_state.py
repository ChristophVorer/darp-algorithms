from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
from uuid import UUID

from darp_algorithms.domain.stop import Stop
from darp_algorithms.domain.request import Request
from darp_algorithms.domain.route import Route
from darp_algorithms.domain.location import Location
from darp_algorithms.domain.violation import Violation
from darp_algorithms.domain.enums.stop_kind import StopKind
from darp_algorithms.domain.enums.violation_type import ViolationType
from .darp_config import DarpConfig

TravelTimeFn = Callable[[Location, Location], timedelta]
TravelDistanceFn = Callable[[Location, Location], float]


@dataclass
class RouteState:
    """
    Routenzustandsstruktur zur iterativen Berechnung der Zulässigkeit einer Route und allen benötigten Metriken zur
    Berechnung des Zielfunktionswerts einer Route.
    """

    # Konfiguration des zugrundeliegenden DARPs
    darp_config: DarpConfig

    # Eingabe-Attribute des Route-States
    route: Route
    # Menge von Anfragen, die der Route zugewiesen ist
    requests: dict[UUID, Request]
    # Funktionen zur Berechnung der Zeiten und Distanzen zwischen den Stopps
    travel_time: TravelTimeFn
    travel_distance: TravelDistanceFn

    # Bool-Variable für den Early-Exit-Mechanismus:
    # Ist dieser Wert True, wird bei der ersten Verletzung einer Nebenbedingung die Berechnung der Routen-Metriken und
    # weitere Zulässigkeitsüberprüfungen unterbrochen.
    early_exit_on_violation: bool = False

    # Berechenbare Attribute einer Route
    arrival: list[datetime] = field(default_factory=list, init=False)
    start_service: list[datetime] = field(default_factory=list, init=False)
    pickup_start_by_req: dict[UUID, datetime] = field(default_factory=dict, init=False)
    delivery_start_by_req: dict[UUID, datetime] = field(default_factory=dict, init=False)
    departure: list[datetime] = field(default_factory=list, init=False)
    load: list[int] = field(default_factory=list, init=False)
    total_travel_time: timedelta = field(default=timedelta(0), init=False)
    total_travel_distance: float = field(default=0, init=False)
    feasible: bool = field(default=True, init=False)
    violations: list[Violation] = field(default_factory=list, init=False)

    def recompute(self) -> None:
        """
        Berechnet iterativ die Zulässigkeit einer Route gemäß der definierten Nebenbedingungen der entsprechenden
        DarpConfig sowie alle für die Berechnung des Zielfunktionswerts einer Route relevanten Metriken.
        """

        # Setze alle aktuellen Werte zurück
        self.arrival.clear()
        self.start_service.clear()
        self.pickup_start_by_req.clear()
        self.delivery_start_by_req.clear()
        self.departure.clear()
        self.load.clear()
        self.total_travel_time = timedelta(0)
        self.total_travel_distance = 0
        self.feasible = True
        self.violations.clear()

        prev_location = self.route.vehicle.start_position
        prev_departure = self.route.vehicle.start_time
        cur_load = 0

        # Start der Neuberechnung aller Routeninformationen
        for index, stop in enumerate(self.route.stops):
            # Zugehörige Anfrage zu dem aktuell betrachteten Stopp
            request = self.requests[stop.request_id]
            request_id = stop.request_id

            # Berechne die Fahrtzeit und Distanz vom letzten berechneten Ort zu dem aktuellen Knoten
            stop_travel_time = self.travel_time(prev_location, stop.location)
            stop_travel_distance = self.travel_distance(prev_location, stop.location)

            # Aktualisiere die Gesamt-Fahrtzeit und Gesamt-Distanz
            self.total_travel_time += stop_travel_time
            self.total_travel_distance += stop_travel_distance

            # Ankunftszeit am aktuellen Knoten
            arrival = prev_departure + stop_travel_time

            # Berechne das einzuhaltende Zeitfenster des Stopps
            earliest_arrival, latest_arrival = self._time_window(stop, request)

            # Zeit zu dem die Bedienung startet
            start_of_service: datetime = max(arrival, earliest_arrival)

            # Zeitfenster-Überprüfung
            if start_of_service > latest_arrival:
                self._add_violation(Violation(ViolationType.TIME_WINDOW, request))
                if self.early_exit_on_violation:
                    break

            # Abfahrtszeitpunkt am aktuellen Knoten
            departure = start_of_service + self.darp_config.service_duration

            if stop.kind == StopKind.PICKUP:
                # Überprüfung, ob der zugehörige Abholknoten bereits eingefügt wurde
                if request_id in self.pickup_start_by_req:
                    self._add_violation(Violation(ViolationType.DOUBLED_PICKUP, request))
                    if self.early_exit_on_violation:
                        break
                self.pickup_start_by_req[request_id] = start_of_service

            elif stop.kind == StopKind.DELIVERY:
                # Überprüfung, ob der zugehörige Abholknoten bereits eingefügt wurde
                if request_id not in self.pickup_start_by_req:
                    self._add_violation(Violation(ViolationType.PRECEDENCE, request))
                    if self.early_exit_on_violation:
                        break
                else:
                    self.delivery_start_by_req[request_id] = start_of_service

                    # Überprüfe die maximale Fahrtzeitbeschränkung, sofern diese definiert ist
                    max_ride_time = self._max_ride_time(request)
                    if max_ride_time is not None:
                        ride_time = start_of_service - self.pickup_start_by_req[request_id]
                        if ride_time > max_ride_time:
                            self._add_violation(Violation(ViolationType.MAX_RIDE_TIME, request))
                            if self.early_exit_on_violation:
                                break

            # Aktualisiere die Beladung des Fahrzeugs
            delta = self._load_delta(stop, request)
            cur_load += delta

            # Überprüfung der Kapazitätsbeschränkung
            if cur_load < 0 or cur_load > self.darp_config.vehicle_capacity:
                self._add_violation(Violation(ViolationType.CAPACITY, request))
                if self.early_exit_on_violation:
                    break

            # Aktualisiere die verbleibenden Attribute der Route entsprechend der berechneten Informationen des Stopps
            self.arrival.append(arrival)
            self.start_service.append(start_of_service)
            self.departure.append(departure)
            self.load.append(cur_load)

            prev_location = stop.location
            prev_departure = departure

    def is_feasible(self) -> bool:
        """
        Gibt zurück, ob die zugehörige Route zulässig gemäß der Nebenbedingung aus der DarpConfig zulässig ist.
        """

        return self.feasible

    def _add_violation(self, violation: Violation) -> None:
        """
        Fügt dem RouteState-Objekt eine Verletzung der Nebenbedingung hinzu.
        """

        self.feasible = False
        self.violations.append(violation)

    @staticmethod
    def _load_delta(stop: Stop, req: Request) -> int:
        """
        Berechnet die Kapazitätsveränderung eines Stopps
        """

        # Abholung der Passagiere => positives Delta
        if stop.kind == StopKind.PICKUP:
            return req.passengers

        # Absetzung der Passagiere => negatives Delta
        if stop.kind == StopKind.DELIVERY:
            return -req.passengers

        raise ValueError(f"Unbekannte Stopp-Art: {stop.kind}")

    def _time_window(self, stop: Stop, req: Request) -> tuple[datetime, datetime]:
        """
        Berechnet die einzuhaltenden Zeitfenster
        """

        # Abhol-Zeitfenster:
        # earliest = Gewünschter Abholzeitpunkt
        # latest = Gewünschter Abholzeitpunkt + Abholpuffer aus der DARP-Konfiguration
        if stop.kind == StopKind.PICKUP:
            desired_pickup_time = req.desired_pickup_time
            earliest = desired_pickup_time
            latest = desired_pickup_time + self.darp_config.pickup_buffer
            return earliest, latest

        # Ziel-Zeitfenster:
        # Aktuell werden keine Zeitfenster für die Zielknoten betrachtet. Daher wird das Zeitfenster unrealistisch groß
        # gesetzt.
        vehicle = self.route.vehicle
        earliest = vehicle.start_time
        latest = vehicle.start_time + timedelta(days=3650)
        return earliest, latest

    def _max_ride_time(self, req: Request) -> Optional[timedelta]:
        """
        Gibt die maximale Fahrtzeit einer Anfrage zurück, sofern die entsprechende Nebenbedingung innerhalb der
        DarpConfig aktiviert ist.
        """
        constraint_config = self.darp_config.constraint_config
        if not constraint_config.use_max_ride_time:
            return None

        # Wenn eine konstante maximale Fahrtzeit definiert wurde, gib diese zurück
        if constraint_config.fixed_max_ride_time is not None:
            return constraint_config.fixed_max_ride_time

        # Wenn ein Faktor für die Berechnung der maximalen Fahrtzeit definiert wurde, nutze diesen Faktor, um die
        # maximale Fahrtzeit zu bestimmen
        if constraint_config.mrt_factor is not None:
            direct_travel_time = self.travel_time(req.pickup, req.delivery)
            mrt_factor = constraint_config.mrt_factor
            return timedelta(seconds=direct_travel_time.total_seconds() * mrt_factor)

        return None
