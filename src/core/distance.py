from __future__ import annotations

import math
from typing import Tuple

EARTH_RADIUS_KM = 6371.0


def haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Great-circle distance between two (lat, lon) pairs in kilometers."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def route_distance(coords: list[Tuple[float, float]]) -> float:
    """Compute total distance for a route that returns to start."""
    if len(coords) < 2:
        return 0.0
    total = 0.0
    for i in range(len(coords) - 1):
        total += haversine(coords[i], coords[i + 1])
    return total
