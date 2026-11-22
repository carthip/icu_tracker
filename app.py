"""
app.py — Streamlit UI for the ICU & Ambulance Tracking agentic system.

Run:
    streamlit run app.py
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from agents.orchestrator_agent import OrchestratorAgent
from data.seed_data import HOSPITALS, AMBULANCES

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ICU & Ambulance Tracker",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f7f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }
    .status-available  { color: #16a34a; font-weight: 600; }
    .status-dispatched { color: #dc2626; font-weight: 600; }
    .status-returning  { color: #d97706; font-weight: 600; }
    .dispatch-box {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 12px;
    }
    .warn-box {
        background: #fff7ed;
        border: 1px solid #fdba74;
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 12px;
    }
    .section-header {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1f2328;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state: one orchestrator per session ───────────────────────────────
def _fresh_orchestrator() -> OrchestratorAgent:
    return OrchestratorAgent(
        hospitals=copy.deepcopy(HOSPITALS),
        ambulances=copy.deepcopy(AMBULANCES),
        radius_km=st.session_state.get("radius_km", 20.0),
    )

if "orc" not in st.session_state:
    st.session_state.orc = _fresh_orchestrator()
if "decisions" not in st.session_state:
    st.session_state.decisions = []
if "patient_counter" not in st.session_state:
    st.session_state.patient_counter = 1


# ── Helpers ───────────────────────────────────────────────────────────────────
STATUS_EMOJI = {"available": "🟢", "dispatched": "🔴", "returning": "🟡"}

def icu_color(avail: int) -> str:
    if avail == 0:
        return "#dc2626"
    if avail <= 3:
        return "#d97706"
    return "#16a34a"

def occupancy_bar(total: int, available: int) -> str:
    pct = int((total - available) / max(total, 1) * 100)
    color = "#dc2626" if pct >= 90 else "#d97706" if pct >= 70 else "#16a34a"
    return f"""
    <div style="background:#e5e7eb;border-radius:4px;height:10px;width:100%;">
      <div style="background:{color};width:{pct}%;height:10px;border-radius:4px;"></div>
    </div>
    <small style="color:#57606a;">{pct}% occupied</small>
    """


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🚑 ICU & Ambulance")
    st.caption("Agentic Dispatch System")
    st.divider()

    st.subheader("🆘 Trigger Emergency")

    patient_id = f"P{st.session_state.patient_counter:03d}"
    st.caption(f"Patient ID: **{patient_id}**")

    lat = st.number_input(
        "Patient Latitude", value=13.0604, format="%.4f",
        min_value=12.5, max_value=13.5, step=0.001,
    )
    lon = st.number_input(
        "Patient Longitude", value=80.2496, format="%.4f",
        min_value=79.5, max_value=80.8, step=0.001,
    )

    st.caption("📍 Quick-pick location:")
    col_a, col_b = st.columns(2)
    if col_a.button("Anna Nagar", use_container_width=True):
        st.session_state["_qlat"], st.session_state["_qlon"] = 13.0850, 80.2101
        st.rerun()
    if col_b.button("Velachery", use_container_width=True):
        st.session_state["_qlat"], st.session_state["_qlon"] = 12.9800, 80.2200
        st.rerun()
    col_c, col_d = st.columns(2)
    if col_c.button("Porur", use_container_width=True):
        st.session_state["_qlat"], st.session_state["_qlon"] = 13.0375, 80.1570
        st.rerun()
    if col_d.button("T. Nagar", use_container_width=True):
        st.session_state["_qlat"], st.session_state["_qlon"] = 13.0418, 80.2341
        st.rerun()

    # Apply quick-pick if set
    if "_qlat" in st.session_state:
        lat = st.session_state.pop("_qlat")
        lon = st.session_state.pop("_qlon")

    radius = st.slider("Search radius (km)", 5, 50, 20, step=5)

    dispatch_btn = st.button("🚨 Dispatch Ambulance", type="primary", use_container_width=True)

    st.divider()
    if st.button("🔄 Reset System", use_container_width=True):
        st.session_state.orc = _fresh_orchestrator()
        st.session_state.decisions = []
        st.session_state.patient_counter = 1
        st.rerun()

    st.divider()
    st.caption("Agents active")
    for a in ["LocationAgent", "ICUAvailabilityAgent", "AmbulanceTrackingAgent",
              "DispatchAgent", "OrchestratorAgent"]:
        st.markdown(f"🤖 `{a}`")


# ── Handle dispatch ───────────────────────────────────────────────────────────
if dispatch_btn:
    orc: OrchestratorAgent = st.session_state.orc
    # Recreate if radius changed
    orc._location_agent._radius_km = radius

    decision = orc.handle_emergency(lat, lon, patient_id)
    st.session_state.decisions.insert(0, {"patient_id": patient_id, "lat": lat, "lon": lon,
                                           **decision})
    st.session_state.patient_counter += 1


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════
st.title("🏥 ICU & Ambulance Tracking")
st.caption("Real-time agentic dispatch — 5 agents · publish/subscribe message bus")
st.divider()

orc: OrchestratorAgent = st.session_state.orc
icu_data   = orc.icu_dashboard()
fleet_data = orc.fleet_dashboard()
bus_msgs   = orc.message_history()

# ── Top KPI strip ─────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
total_icu   = sum(h["icu_total"]     for h in icu_data)
avail_icu   = sum(h["icu_available"] for h in icu_data)
amb_avail   = sum(1 for a in fleet_data if a["status"] == "available")
amb_disp    = sum(1 for a in fleet_data if a["status"] == "dispatched")
dispatches  = len(st.session_state.decisions)

k1.metric("🛏️ Total ICU Beds",      total_icu)
k2.metric("✅ ICU Available",        avail_icu,  delta=f"{avail_icu - (total_icu - avail_icu)} vs occupied")
k3.metric("🚑 Ambulances Available", amb_avail)
k4.metric("🔴 Ambulances Dispatched", amb_disp)
k5.metric("📋 Total Dispatches",     dispatches)

st.divider()

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

# ── LEFT: ICU Dashboard ───────────────────────────────────────────────────────
with left:
    st.markdown('<p class="section-header">🏥 Hospital ICU Status</p>', unsafe_allow_html=True)
    for h in icu_data:
        avail  = h["icu_available"]
        total  = h["icu_total"]
        color  = icu_color(avail)
        occ_bar = occupancy_bar(total, avail)
        st.markdown(f"""
        <div class="metric-card">
          <strong>{h['name']}</strong><br>
          <span style="color:{color};font-size:1.1rem;font-weight:700;">{avail}</span>
          <span style="color:#57606a;"> / {total} ICU beds free</span><br><br>
          {occ_bar}
        </div>
        """, unsafe_allow_html=True)

# ── RIGHT: Ambulance Fleet ────────────────────────────────────────────────────
with right:
    st.markdown('<p class="section-header">🚑 Ambulance Fleet</p>', unsafe_allow_html=True)
    for a in fleet_data:
        emoji  = STATUS_EMOJI.get(a["status"], "⚪")
        css_cl = f"status-{a['status']}"
        hosp   = a["assigned_to"] or "—"
        st.markdown(f"""
        <div class="metric-card">
          <strong>{a['name']}</strong>
          &nbsp;&nbsp;{emoji}&nbsp;<span class="{css_cl}">{a['status'].upper()}</span><br>
          <span style="color:#57606a;">📍 ({a['lat']:.4f}, {a['lon']:.4f})</span><br>
          <span style="color:#57606a;">🏥 Assigned: <strong>{hosp}</strong></span>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Dispatch History ──────────────────────────────────────────────────────────
st.markdown('<p class="section-header">📋 Dispatch History</p>', unsafe_allow_html=True)

if not st.session_state.decisions:
    st.info("No dispatches yet — use the sidebar to trigger an emergency.")
else:
    for d in st.session_state.decisions:
        status = d.get("status", "unknown")
        pid    = d.get("patient_id", "?")
        plat   = d.get("lat", 0)
        plon   = d.get("lon", 0)

        if status == "dispatched":
            hosp  = d["hospital"]
            amb   = d["ambulance"]
            st.markdown(f"""
            <div class="dispatch-box">
              <strong>✅ {pid}</strong> — dispatched successfully<br>
              📍 Patient: ({plat:.4f}, {plon:.4f})<br>
              🏥 Hospital: <strong>{hosp['name']}</strong>
                 &nbsp;·&nbsp; {hosp['distance_km']} km away
                 &nbsp;·&nbsp; {hosp['icu_available']} ICU beds remaining<br>
              🚑 Ambulance: <strong>{amb['name']}</strong>
                 &nbsp;·&nbsp; {amb['distance_to_hospital_km']} km to hospital
            </div>
            """, unsafe_allow_html=True)
        else:
            reason = status.replace("_", " ").title()
            st.markdown(f"""
            <div class="warn-box">
              <strong>⚠️ {pid}</strong> — {reason}<br>
              📍 Patient: ({plat:.4f}, {plon:.4f})
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Message Bus Log ───────────────────────────────────────────────────────────
with st.expander(f"📨 Message Bus Log ({len(bus_msgs)} messages)", expanded=False):
    if bus_msgs:
        topic_filter = st.selectbox(
            "Filter by topic",
            ["All"] + sorted({m["topic"] for m in bus_msgs}),
            key="topic_filter",
        )
        shown = bus_msgs if topic_filter == "All" else [m for m in bus_msgs if m["topic"] == topic_filter]
        for msg in reversed(shown):
            topic = msg["topic"]
            rest  = {k: v for k, v in msg.items() if k != "topic"}
            st.markdown(f"**`{topic}`**")
            st.json(rest, expanded=False)
    else:
        st.caption("No messages yet.")
