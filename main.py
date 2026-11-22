"""
main.py — Entry point for the ICU & Ambulance Tracking agentic system.

Run:
    python main.py

Demonstrates the full agentic loop with three sample emergencies.
"""

import json
import logging
import sys
import os

# Allow imports from the project root
sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator_agent import OrchestratorAgent

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)

DIVIDER = "─" * 60


def print_json(label: str, data: object) -> None:
    print(f"\n{label}")
    print(json.dumps(data, indent=2, default=str))


def run_demo() -> None:
    print(f"\n{'═' * 60}")
    print("   ICU & AMBULANCE TRACKING — AGENTIC SYSTEM DEMO")
    print(f"{'═' * 60}")

    orchestrator = OrchestratorAgent(radius_km=20.0)

    # ── Initial dashboards ──────────────────────────────────────────
    print_json("📋  ICU Dashboard (initial state):", orchestrator.icu_dashboard())
    print_json("🚑  Fleet Dashboard (initial state):", orchestrator.fleet_dashboard())

    # ── Emergency 1 ────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("🆘  EMERGENCY 1 — patient near Anna Nagar (13.0850, 80.2101)")
    print(DIVIDER)
    decision1 = orchestrator.handle_emergency(13.0850, 80.2101, "P001")
    print_json("✅  Dispatch Decision:", decision1)

    # ── Emergency 2 ────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("🆘  EMERGENCY 2 — patient near Velachery (12.9800, 80.2200)")
    print(DIVIDER)
    decision2 = orchestrator.handle_emergency(12.9800, 80.2200, "P002")
    print_json("✅  Dispatch Decision:", decision2)

    # ── Emergency 3 ────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("🆘  EMERGENCY 3 — patient near Porur (13.0375, 80.1570)")
    print(DIVIDER)
    decision3 = orchestrator.handle_emergency(13.0375, 80.1570, "P003")
    print_json("✅  Dispatch Decision:", decision3)

    # ── Post-dispatch dashboards ────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("📊  State after all dispatches")
    print(DIVIDER)
    print_json("📋  ICU Dashboard (updated):", orchestrator.icu_dashboard())
    print_json("🚑  Fleet Dashboard (updated):", orchestrator.fleet_dashboard())

    # ── Message bus summary ─────────────────────────────────────────
    print(f"\n{DIVIDER}")
    history = orchestrator.message_history()
    print(f"📨  Total messages on bus: {len(history)}")
    topics = {}
    for m in history:
        topics[m["topic"]] = topics.get(m["topic"], 0) + 1
    for topic, count in sorted(topics.items()):
        print(f"    {topic:35s} × {count}")

    print(f"\n{'═' * 60}")
    print("   Demo complete.")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    run_demo()
