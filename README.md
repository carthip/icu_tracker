# ICU & Ambulance Tracking — Agentic System

A minimal **five-agent** Python system that tracks ICU bed availability and ambulance
fleet status to intelligently dispatch the nearest ambulance to the best available
hospital for a patient in emergency.

---

## Architecture

```
Patient Emergency Call
        │
        ▼
┌─────────────────────┐
│  OrchestratorAgent  │  ← Agent 5 — wires everything, single entry point
└──────────┬──────────┘
           │ handle_emergency(lat, lon, patient_id)
           ▼
┌─────────────────────┐
│   LocationAgent     │  ← Agent 1 — resolves GPS, finds nearby hospitals
└──────────┬──────────┘
           │ publishes: location.resolved
           ▼
┌──────────────────────────┐
│  ICUAvailabilityAgent    │  ← Agent 2 — filters hospitals with free ICU beds
└──────────┬───────────────┘
           │ publishes: icu.availability.report
           ▼
┌──────────────────────────┐
│     DispatchAgent        │  ← Agent 4 — scores hospitals, picks best ambulance
└──────────┬───────────────┘
           │ asks: AmbulanceTrackingAgent   (← Agent 3)
           │ publishes: dispatch.decision
           ▼
     Final Decision
```

### Message Topics

| Topic | Publisher | Subscriber(s) |
|---|---|---|
| `location.resolved` | LocationAgent | ICUAvailabilityAgent |
| `icu.availability.report` | ICUAvailabilityAgent | DispatchAgent |
| `icu.bed.reserved` | ICUAvailabilityAgent | (logging) |
| `ambulance.status.update` | AmbulanceTrackingAgent | (logging) |
| `dispatch.decision` | DispatchAgent | OrchestratorAgent |

---

## Project Layout

```
icu_ambulance_tracker/
├── agents/
│   ├── location_agent.py          # Agent 1
│   ├── icu_availability_agent.py  # Agent 2
│   ├── ambulance_tracking_agent.py# Agent 3
│   ├── dispatch_agent.py          # Agent 4
│   └── orchestrator_agent.py      # Agent 5
├── data/
│   └── seed_data.py               # Hospitals & ambulances (Chennai region)
├── utils/
│   ├── distance.py                # Haversine distance
│   └── message_bus.py             # Publish/subscribe message bus
├── tests/
│   └── test_system.py             # Pytest unit + integration tests
├── main.py                        # Demo entry point
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# No external dependencies required — pure Python 3.11+
cd icu_ambulance_tracker
python main.py
```

### Run tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Extending the System

| Goal | How |
|---|---|
| Real GPS input | Replace `LocationAgent._simulate_reverse_geocode` with a geocoder API call |
| Live hospital data | Replace `seed_data.py` with a database / REST client in `ICUAvailabilityAgent` |
| Live ambulance telemetry | Call `AmbulanceTrackingAgent.update_position()` from a WebSocket feed |
| Persistent decisions | Subscribe to `dispatch.decision` and write to a DB in `OrchestratorAgent` |
| REST API | Wrap `OrchestratorAgent.handle_emergency()` in a FastAPI endpoint |

---

## Dispatch Scoring

The `DispatchAgent` ranks hospitals using a weighted composite score:

```
score = 0.50 × (1 − normalised_distance)
      + 0.30 × normalised_icu_beds
      + 0.20 × (1 − normalised_occupancy)
```

Weights can be tuned directly in [`dispatch_agent.py`](agents/dispatch_agent.py).
