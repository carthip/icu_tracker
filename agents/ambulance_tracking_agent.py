"""
Agent 3 — AmbulanceTrackingAgent
----------------------------------
Responsibilities:
  - Maintain real-time positions and statuses of the ambulance fleet.
  - Find the closest available ambulance to a given coordinate.
  - Update ambulance status (available / dispatched / returning).
  - Publish 'ambulance.status.update' events on state changes.
"""

import logging
from typing import Any

from utils.distance import haversine_distance
from utils.message_bus import MessageBus

logger = logging.getLogger(__name__)

# Valid status transitions
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "available":  {"dispatched"},
    "dispatched": {"returning", "available"},
    "returning":  {"available"},
}


class AmbulanceTrackingAgent:
    """Tracks ambulance fleet positions and manages dispatch status."""

    NAME = "AmbulanceTrackingAgent"

    def __init__(self, bus: MessageBus, ambulances: list[dict]) -> None:
        self._bus = bus
        self._fleet: dict[str, dict] = {a["id"]: dict(a) for a in ambulances}
        logger.info("[%s] initialised with %d ambulances", self.NAME, len(self._fleet))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_available_ambulances(self) -> list[dict]:
        """Return all ambulances whose status is 'available'."""
        return [a for a in self._fleet.values() if a["status"] == "available"]

    def find_nearest_available(self, lat: float, lon: float) -> dict | None:
        """
        Return the nearest available ambulance to (lat, lon), or None if none free.
        """
        candidates = self.get_available_ambulances()
        if not candidates:
            logger.warning("[%s] No available ambulances in fleet", self.NAME)
            return None

        nearest = min(
            candidates,
            key=lambda a: haversine_distance(lat, lon, a["lat"], a["lon"]),
        )
        nearest["distance_km"] = round(
            haversine_distance(lat, lon, nearest["lat"], nearest["lon"]), 2
        )
        return nearest

    def update_position(self, ambulance_id: str, lat: float, lon: float) -> None:
        """Update GPS coordinates for an ambulance (called periodically by telemetry)."""
        amb = self._fleet.get(ambulance_id)
        if amb:
            amb["lat"], amb["lon"] = lat, lon
            logger.debug("[%s] %s position updated → (%.4f, %.4f)", self.NAME, ambulance_id, lat, lon)

    def update_status(self, ambulance_id: str, new_status: str, assigned_to: str | None = None) -> bool:
        """
        Transition an ambulance to *new_status*.
        Returns False and logs a warning if the transition is invalid.
        """
        amb = self._fleet.get(ambulance_id)
        if not amb:
            logger.error("[%s] Unknown ambulance id: %s", self.NAME, ambulance_id)
            return False

        current = amb["status"]
        if new_status not in _VALID_TRANSITIONS.get(current, set()):
            logger.warning(
                "[%s] Invalid transition %s → %s for %s",
                self.NAME, current, new_status, ambulance_id,
            )
            return False

        amb["status"] = new_status
        amb["assigned_to"] = assigned_to

        payload: dict[str, Any] = {
            "ambulance_id": ambulance_id,
            "ambulance_name": amb["name"],
            "previous_status": current,
            "new_status": new_status,
            "assigned_to": assigned_to,
            "lat": amb["lat"],
            "lon": amb["lon"],
        }
        self._bus.publish("ambulance.status.update", payload)
        logger.info(
            "[%s] %s: %s → %s (hospital: %s)",
            self.NAME, ambulance_id, current, new_status, assigned_to,
        )
        return True

    def fleet_report(self) -> list[dict]:
        """Return a snapshot of the entire fleet."""
        return [
            {
                "id": a["id"],
                "name": a["name"],
                "status": a["status"],
                "assigned_to": a["assigned_to"],
                "lat": a["lat"],
                "lon": a["lon"],
            }
            for a in self._fleet.values()
        ]
