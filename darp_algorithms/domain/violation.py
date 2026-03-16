from dataclasses import dataclass

from .enums.violation_type import ViolationType
from .request import Request


@dataclass(frozen=True, slots=True)
class Violation:
    type: ViolationType
    request: Request
