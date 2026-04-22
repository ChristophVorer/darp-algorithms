from __future__ import annotations

from enum import Enum


class StopKind(str, Enum):
    """
    Definiert die Art eines Stopps.(Pickup/Delivery)
    """

    PICKUP = "pickup"
    DELIVERY = "delivery"
