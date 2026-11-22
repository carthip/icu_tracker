"""
Agent 5 — OrchestratorAgent
-----------------------------
Responsibilities:
  - Bootstrap all agents in the correct dependency order.
  - Expose a single `handle_emergency(lat, lon, patient_id)` entry point.
  - Collect and display the final dispatch decision.
  - Provide status dashboards for ICU and fleet.
  - Optionally run a demo simulation with multiple patients.
"""

import logging
from typing import Any

from utils.message_bus import MessageBus
from data.seed_data import HOSPITALS, AMBULANCES
from agents.location_agent import LocationAgent
from agents.icu_availability_agent import ICUAvailabilityAgent
from agents.ambulance_tracking_agent import AmbulanceTrackingAgent
from agents.dispatch_agent import DispatchAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Top-level agent that wires up the system and drives the agentic loop.

    Wiring order (dependency graph):
        MessageBus
            ↓
        ICUAvailabilityAgent  ←── subscribes to 'location.resolved'
        AmbulanceTrackingAgent
            ↓
        DispatchAgent         ←── subscribes to 'icu.availability.report'
            ↓
        LocationAgent         (triggers the chain when resolve() is called)
    """

    NAME = "OrchestratorAgent"

    def __init__(
        self,
        hospitals: list[dict] | None = None,
        ambulances: list[dict] | None = None,
        radius_km: float = 20.0,
    ) -> None:
        self._bus = MessageBus()

        # Build agents
        self._icu_agent = ICUAvailabilityAgent(self._bus, hospitals or HOSPITALS)
        self._ambulance_agent = AmbulanceTrackingAgent(self._bus, ambulances or AMBULANCES)
        self._dispatch_agent = DispatchAgent(self._bus, self._icu_agent, self._ambulance_agent)
        self._location_agent = LocationAgent(self._bus, hospitals or HOSPITALS, radius_km)

        # Capture dispatch decisions for callers
        self._last_decision: dict | None = None
        self._bus.subscribe("dispatch.decision", self._on_decision)

        logger.info("[%s] all agents initialised and wired", self.NAME)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_emergency(
        self, patient_lat: float, patient_lon: float, patient_id: str = "P001"
    ) -> dict[str, Any]:
        """
        Main agentic loop entry point.

        1. LocationAgent resolves position → triggers 'location.resolved'
        2. ICUAvailabilityAgent reacts → triggers 'icu.availability.report'
        3. DispatchAgent reacts → triggers 'dispatch.decision'
        4. OrchestratorAgent captures and returns the decision.
        """
        logger.info(
            "[%s] ── EMERGENCY ── patient=%s lat=%.4f lon=%.4f",
            self.NAME, patient_id, patient_lat, patient_lon,
        )
        self._last_decision = None
        self._location_agent.resolve(patient_lat, patient_lon, patient_id)
        return self._last_decision or {"patient_id": patient_id, "status": "unresolved"}

    def icu_dashboard(self) -> list[dict]:
        """Return the current ICU availability for all hospitals."""
        return self._icu_agent.status_report()

    def fleet_dashboard(self) -> list[dict]:
        """Return the current status of the ambulance fleet."""
        return self._ambulance_agent.fleet_report()

    def message_history(self, topic: str | None = None) -> list[dict]:
        """Return all messages published on the bus (optionally filtered)."""
        return self._bus.get_history(topic)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_decision(self, message: dict) -> None:
        self._last_decision = message
