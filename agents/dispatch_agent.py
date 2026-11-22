"""
Agent 4 — DispatchAgent
-------------------------
Responsibilities:
  - Subscribe to 'icu.availability.report' events.
  - Score candidate hospitals using a composite metric
    (ICU beds available, distance, occupancy).
  - Ask AmbulanceTrackingAgent for the nearest free ambulance.
  - Issue a dispatch decision and publish 'dispatch.decision' event.
  - Confirm the dispatch by updating ambulance status and reserving the ICU bed.
"""

import logging
from typing import Any

from utils.message_bus import MessageBus
from agents.icu_availability_agent import ICUAvailabilityAgent
from agents.ambulance_tracking_agent import AmbulanceTrackingAgent

logger = logging.getLogger(__name__)

# Scoring weights (must sum to 1.0)
W_DISTANCE = 0.50
W_ICU_BEDS = 0.30
W_OCCUPANCY = 0.20


class DispatchAgent:
    """
    Decides which hospital to target and which ambulance to dispatch.
    Uses a normalised composite score to rank candidates.
    """

    NAME = "DispatchAgent"

    def __init__(
        self,
        bus: MessageBus,
        icu_agent: ICUAvailabilityAgent,
        ambulance_agent: AmbulanceTrackingAgent,
    ) -> None:
        self._bus = bus
        self._icu_agent = icu_agent
        self._ambulance_agent = ambulance_agent

        self._bus.subscribe("icu.availability.report", self._on_icu_report)
        logger.info("[%s] initialised", self.NAME)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_icu_report(self, message: dict) -> None:
        patient_id = message["patient_id"]
        candidates = message.get("available_hospitals", [])

        if not candidates:
            logger.warning("[%s] No ICU-available hospitals for patient %s", self.NAME, patient_id)
            self._bus.publish(
                "dispatch.decision",
                {"patient_id": patient_id, "status": "no_hospital_available"},
            )
            return

        best_hospital = self._rank_hospitals(candidates)
        ambulance = self._ambulance_agent.find_nearest_available(
            best_hospital["lat"], best_hospital["lon"]
        )

        if not ambulance:
            logger.warning("[%s] No available ambulances for patient %s", self.NAME, patient_id)
            self._bus.publish(
                "dispatch.decision",
                {"patient_id": patient_id, "status": "no_ambulance_available",
                 "target_hospital": best_hospital["name"]},
            )
            return

        # Commit: reserve ICU bed + update ambulance status
        self._icu_agent.reserve_bed(best_hospital["id"])
        self._ambulance_agent.update_status(ambulance["id"], "dispatched", best_hospital["id"])

        payload: dict[str, Any] = {
            "patient_id": patient_id,
            "status": "dispatched",
            "hospital": {
                "id": best_hospital["id"],
                "name": best_hospital["name"],
                "distance_km": best_hospital.get("distance_km"),
                "icu_available": best_hospital["icu_available"],
            },
            "ambulance": {
                "id": ambulance["id"],
                "name": ambulance["name"],
                "distance_to_hospital_km": ambulance.get("distance_km"),
            },
        }
        self._bus.publish("dispatch.decision", payload)
        logger.info(
            "[%s] DISPATCHED %s → %s for patient %s",
            self.NAME, ambulance["id"], best_hospital["name"], patient_id,
        )

    # ------------------------------------------------------------------
    # Scoring logic
    # ------------------------------------------------------------------

    def _rank_hospitals(self, candidates: list[dict]) -> dict:
        """
        Score each hospital and return the best one.

        Score = W_DISTANCE * (1 - norm_dist) + W_ICU_BEDS * norm_beds + W_OCCUPANCY * (1 - norm_occ)
        Lower distance, higher bed count, lower occupancy → better score.
        """
        if len(candidates) == 1:
            return candidates[0]

        distances = [h.get("distance_km") or 0 for h in candidates]
        beds = [h["icu_available"] for h in candidates]
        occupancies = [
            (h["icu_total"] - h["icu_available"]) / max(h["icu_total"], 1)
            for h in candidates
        ]

        max_dist = max(distances) or 1
        max_beds = max(beds) or 1
        max_occ = max(occupancies) or 1

        scored = []
        for h, d, b, o in zip(candidates, distances, beds, occupancies):
            score = (
                W_DISTANCE * (1 - d / max_dist)
                + W_ICU_BEDS * (b / max_beds)
                + W_OCCUPANCY * (1 - o / max_occ)
            )
            scored.append((score, h))

        scored.sort(key=lambda x: x[0], reverse=True)
        logger.debug("[%s] Hospital scores: %s", self.NAME, [(round(s, 3), h["name"]) for s, h in scored])
        return scored[0][1]
