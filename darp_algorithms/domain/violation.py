from dataclasses import dataclass

from .enums.violation_type import ViolationType
from .request import Request


@dataclass(frozen=True, slots=True)
class Violation:
    """
    Domain-Klasse zur Repräsentation einer Nebenbedingunsgverletzung.

    Enthält Informationen über den Typ der Verletzung und die Anfrage, die die Verletzung verursacht hat.
    """

    type: ViolationType
    request: Request
