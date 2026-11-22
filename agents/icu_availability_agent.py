"""
Agent 2 — ICUAvailabilityAgent
--------------------------------
Responsibilities:
  - Maintain a live registry of ICU bed counts per hospital.
  - Subscribe to 'location.resolved' events and filter hospitals with free ICU beds.
  - Provide reserve/release operations so bed counts stay accurate.
  - Publish 'icu.availability.report' events with available hospitals.
"""

import logging
from typing import Any

from utils.message_bus import MessageBus

logger = logging.getLogger(__name__)


class ICUAvailabilityAgent:
    """Tracks ICU bed availability and responds to location events."""

    NAME = "ICUAvailabilityAgent"

    def __init__(self, bus: MessageBus, hospitals: list[dict]) -> None:
        self._bus = bus
        # Keyed by hospital id for O(1) lookup
        self._registry: dict[str, dict] = {h["id"]: dict(h) for h in hospitals}

        # React whenever the location agent resolves a patient position
        self._bus.subscribe("location.resolved", self._on_location_resolved)
        logger.info("[%s] initialised with %d hospitals", self.NAME, len(self._registry))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_available_hospitals(self, hospital_ids: list[str] | None = None) -> list[dict]:
        """
        Return hospitals that have at least one free ICU bed.
        If *hospital_ids* is provided only those are checked.
        """
        candidates = (
            [self._registry[hid] for hid in hospital_ids if hid in self._registry]
            if hospital_ids
            else list(self._registry.values())
        )
        return [h for h in candidates if h["icu_available"] > 0]

    def reserve_bed(self, hospital_id: str) -> bool:
        """Decrement ICU available count. Returns True on success."""
        hospital = self._registry.get(hospital_id)
        if hospital and hospital["icu_available"] > 0:
            hospital["icu_available"] -= 1
            logger.info(
                "[%s] Reserved ICU bed at %s (remaining: %d)",
                self.NAME, hospital["name"], hospital["icu_available"],
            )
            self._bus.publish(
                "icu.bed.reserved",
                {"hospital_id": hospital_id, "hospital_name": hospital["name"],
                 "icu_available": hospital["icu_available"]},
            )
            return True
        logger.warning("[%s] Cannot reserve bed at %s — none available", self.NAME, hospital_id)
        return False

    def release_bed(self, hospital_id: str) -> None:
        """Increment ICU available count (patient discharged / transfer cancelled)."""
        hospital = self._registry.get(hospital_id)
        if hospital:
            hospital["icu_available"] = min(hospital["icu_available"] + 1, hospital["icu_total"])
            logger.info(
                "[%s] Released ICU bed at %s (available: %d)",
                self.NAME, hospital["name"], hospital["icu_available"],
            )

    def status_report(self) -> list[dict]:
        """Return a snapshot of all ICU counts."""
        return [
            {
                "id": h["id"],
                "name": h["name"],
                "icu_total": h["icu_total"],
                "icu_available": h["icu_available"],
                "occupancy_pct": round(
                    (h["icu_total"] - h["icu_available"]) / h["icu_total"] * 100, 1
                ),
            }
            for h in self._registry.values()
        ]

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_location_resolved(self, message: dict) -> None:
        """Filter nearby hospitals by ICU availability and publish a report."""
        nearby_ids = [h["id"] for h in message.get("nearby_hospitals", [])]
        available = self.get_available_hospitals(nearby_ids)

        # Attach distance info from the original location message
        dist_map = {h["id"]: h.get("distance_km") for h in message.get("nearby_hospitals", [])}
        for h in available:
            h["distance_km"] = dist_map.get(h["id"])

        payload: dict[str, Any] = {
            "patient_id": message["patient_id"],
            "available_hospitals": available,
        }
        self._bus.publish("icu.availability.report", payload)
        logger.info(
            "[%s] %d hospitals with free ICU beds for patient %s",
            self.NAME, len(available), message["patient_id"],
        )
