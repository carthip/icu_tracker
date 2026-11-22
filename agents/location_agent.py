"""
Agent 1 — LocationAgent
------------------------
Responsibilities:
  - Accept a patient's raw GPS coordinates (lat, lon).
  - Resolve a human-readable address (simulated here).
  - Find the nearest hospitals within a configurable radius.
  - Publish a 'location.resolved' event on the message bus.
"""

import logging
from typing import Any

from utils.distance import haversine_distance
from utils.message_bus import MessageBus

logger = logging.getLogger(__name__)


class LocationAgent:
    """Resolves patient location and surfaces nearby hospitals."""

    NAME = "LocationAgent"

    def __init__(self, bus: MessageBus, hospitals: list[dict], radius_km: float = 20.0) -> None:
        self._bus = bus
        self._hospitals = hospitals
        self._radius_km = radius_km
        logger.info("[%s] initialised (search radius: %.1f km)", self.NAME, radius_km)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, patient_lat: float, patient_lon: float, patient_id: str = "P001") -> dict:
        """
        Resolve the patient's location and return nearby hospitals sorted by distance.

        Returns a dict published on the 'location.resolved' topic.
        """
        logger.info(
            "[%s] Resolving location for %s → (%.4f, %.4f)",
            self.NAME, patient_id, patient_lat, patient_lon,
        )

        nearby = self._find_nearby_hospitals(patient_lat, patient_lon)

        payload: dict[str, Any] = {
            "patient_id": patient_id,
            "patient_lat": patient_lat,
            "patient_lon": patient_lon,
            "address": self._simulate_reverse_geocode(patient_lat, patient_lon),
            "nearby_hospitals": nearby,
        }

        self._bus.publish("location.resolved", payload)
        logger.info(
            "[%s] Found %d hospitals within %.1f km", self.NAME, len(nearby), self._radius_km
        )
        return payload

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_nearby_hospitals(self, lat: float, lon: float) -> list[dict]:
        results = []
        for hospital in self._hospitals:
            dist = haversine_distance(lat, lon, hospital["lat"], hospital["lon"])
            if dist <= self._radius_km:
                results.append({**hospital, "distance_km": round(dist, 2)})
        results.sort(key=lambda h: h["distance_km"])
        return results

    @staticmethod
    def _simulate_reverse_geocode(lat: float, lon: float) -> str:
        """Return a placeholder address string (replace with a real geocoder API)."""
        return f"Approx. location at ({lat:.4f}, {lon:.4f}), Chennai, India"
