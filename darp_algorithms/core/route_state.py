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
    Routen-Solver zur Berechnung der Feasibility einer Route und allen benötigten Metriken zur Berechnung der
    Zielfunktion einer gesamten Route
    """

    # Konfiguration des zugrundeliegenden DARPs
    darp_config: DarpConfig

    # Eingabe-Attribute des Route-States
    route: Route
    requests: dict[UUID, Request]
    travel_time: TravelTimeFn
    travel_distance: TravelDistanceFn

    # Bool-Variable für den Early-Exit-Mechanismus
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
        Berechnet für die Nebenbedingungen und Zielfunktion relevante Metriken einer Route
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

        prev_loc = self.route.vehicle.start_position
        prev_dep = self.route.vehicle.start_time
        cur_load = 0

        # Start der Neuberechnung aller Routeninformationen
        for index, stop in enumerate(self.route.stops):
            # Zugehörige Anfrage zu dem aktuell betrachteten Stopp
            req = self.requests[stop.request_id]
            req_id = stop.request_id

            # Berechne die Fahrtzeit und Distanz vom letzten berechneten Ort zu dem aktuellen Knoten
            stop_travel_time = self.travel_time(prev_loc, stop.location)
            stop_travel_distance = self.travel_distance(prev_loc, stop.location)

            # Aktualisiere die Gesamt-Fahrtzeit und Gesamt-Distanz
            self.total_travel_time += stop_travel_time
            self.total_travel_distance += stop_travel_distance

            # Ankunftszeit am aktuellen Knoten
            arrival = prev_dep + stop_travel_time

            # Berechne das einzuhaltende Zeitfenster des Stopps
            earliest_arrival, latest_arrival = self._time_window(stop, req)

            # Zeit zu dem die Service-Zeit beginnt
            start_of_service: datetime = max(arrival, earliest_arrival)

            # BOF Zeitfenster-Überprüfung
            if start_of_service > latest_arrival:
                self._add_violation(Violation(ViolationType.TIME_WINDOW, req))
                if self.early_exit_on_violation:
                    break
            # EOF Zeitfenster-Überprüfung

            # Abfahrtszeitpunkt am aktuellen Knoten
            departure = start_of_service + self.darp_config.service_duration

            if stop.kind == StopKind.PICKUP:
                if req_id in self.pickup_start_by_req:
                    self._add_violation(Violation(ViolationType.DOUBLED_PICKUP, req))
                    if self.early_exit_on_violation:
                        break
                self.pickup_start_by_req[req_id] = start_of_service

            elif stop.kind == StopKind.DELIVERY:
                # Überprüfung, ob der zugehörige Abholknoten bereits eingefügt wurde
                if req_id not in self.pickup_start_by_req:
                    self._add_violation(Violation(ViolationType.PRECEDENCE, req))
                    if self.early_exit_on_violation:
                        break
                else:
                    self.delivery_start_by_req[req_id] = start_of_service

                    max_ride_time = self._max_ride_time(req)
                    if max_ride_time is not None:
                        ride_time = start_of_service - self.pickup_start_by_req[req_id]
                        if ride_time > max_ride_time:
                            self._add_violation(Violation(ViolationType.MAX_RIDE_TIME, req))
                            if self.early_exit_on_violation:
                                break

            # Aktualisiere die Beladung des Fahrzeugs
            delta = self._load_delta(stop, req)
            cur_load += delta

            # BOF Kapazitätsüberprüfung
            if cur_load < 0 or cur_load > self.darp_config.vehicle_capacity:
                self._add_violation(Violation(ViolationType.CAPACITY, req))
                if self.early_exit_on_violation:
                    break
            # EOF Kapazitätsüberprüfung

            # Aktualisiere die Attribute der Route entsprechend der berechneten Informationen des Stopps
            self.arrival.append(arrival)
            self.start_service.append(start_of_service)
            self.departure.append(departure)
            self.load.append(cur_load)

            prev_loc = stop.location
            prev_dep = departure

    def is_feasible(self) -> bool:
        return self.feasible

    def _add_violation(self, violation: Violation) -> None:
        self.feasible = False
        self.violations.append(violation)

    def _load_delta(self, stop: Stop, req: Request) -> int:
        """
        Berechnet die Kapazitätsänderung eines Stopps
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

        """ 
        Abhol-Zeitfenster
        earliest = Gewünschter Abholzeitpunkt
        latest = Gewünschter Abholzeitpunkt + Abholpuffer aus der DARP Konfiguration
        """
        if stop.kind == StopKind.PICKUP:
            desired_pickup_time = req.desired_pickup_time
            earliest = desired_pickup_time
            latest = desired_pickup_time + self.darp_config.pickup_buffer
            return earliest, latest

        """
        Ziel-Zeitfenster
        Aktuell werden keine Zeitfenster für die Zielknoten betrachtet. Daher wird das Zeitfenster unrealistisch groß
        gesetzt.
        """
        vehicle = self.route.vehicle
        earliest = vehicle.start_time
        latest = vehicle.start_time + timedelta(days=3650)
        return earliest, latest

    def _max_ride_time(self, req: Request) -> Optional[timedelta]:
        """
        Gibt die maximale Fahrtzeit einer Anfrage zurück, sofern Sie aktiviert ist
        """
        constraint_config = self.darp_config.constraint_config
        if not constraint_config.use_max_ride_time:
            return None

        # Wenn eine konstante maximale Fahrtzeit definiert wurde, gib diese zurück
        if constraint_config.fixed_max_ride_time is not None:
            return constraint_config.fixed_max_ride_time

        """
        Wenn ein Faktor für die Berechnung der maximalen Fahrtzeit definiert wurde, nutze diesen Faktor, um die
        maximale Fahrtzeit zu bestimmen
        """
        if constraint_config.mrt_factor is not None:
            direct_travel_time = self.travel_time(req.pickup, req.delivery)
            mrt_factor = constraint_config.mrt_factor
            return timedelta(seconds=direct_travel_time.total_seconds() * mrt_factor)

        return None
