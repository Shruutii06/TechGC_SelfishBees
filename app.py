"""
Conference Organizer — Streamlit Web UI
Run with: streamlit run app.py
"""

import streamlit as st
import json
import os
import time
from dotenv import load_dotenv
load_dotenv()

from validator import validate_and_normalise, ValidationError, print_supported_options
from config import SUPPORTED_SPORTS, SUPPORTED_GEOGRAPHIES
from orchestrator import run_pipeline

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EventForge AI",
    page_icon="🏟️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background: #0A0A0F;
    color: #E8E8F0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111118 !important;
    border-right: 1px solid #1E1E2E;
}

/* Hero */
.hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
    border-bottom: 1px solid #1E1E2E;
    margin-bottom: 2rem;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #E8E8F0 0%, #7B7BFF 50%, #FF6B6B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.5rem;
    letter-spacing: -1px;
}
.hero p {
    color: #6E6E8A;
    font-size: 1.05rem;
    font-weight: 300;
    margin: 0;
}

/* Cards */
.result-card {
    background: #111118;
    border: 1px solid #1E1E2E;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.result-card h3 {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #7B7BFF;
    margin: 0 0 1rem;
}

/* Sponsor pills */
.pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.pill {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 500;
}
.pill-title  { background: #2A1F5C; color: #A89FFF; border: 1px solid #3D3080; }
.pill-gold   { background: #2A2010; color: #D4A84B; border: 1px solid #4A3A1A; }
.pill-silver { background: #1A1A2A; color: #8888AA; border: 1px solid #2A2A3A; }

/* Speaker cards */
.speaker-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px,1fr)); gap: 10px; }
.speaker-item {
    background: #16161F;
    border: 1px solid #1E1E2E;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}
.speaker-avatar {
    width: 48px; height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7B7BFF, #FF6B6B);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 10px;
    font-size: 1.2rem;
}
.speaker-name  { font-size: 0.88rem; font-weight: 500; color: #E8E8F0; margin-bottom: 3px; }
.speaker-sport { font-size: 0.75rem; color: #6E6E8A; }
.speaker-tag   { font-size: 0.7rem; color: #7B7BFF; margin-top: 6px; }

/* Venue badge */
.venue-top {
    background: linear-gradient(135deg, #0F1A2E, #162040);
    border: 1px solid #1E3A6E;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 10px;
}
.venue-name  { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; color: #6BA3FF; }
.venue-meta  { font-size: 0.82rem; color: #6E6E8A; margin-top: 4px; }

/* Pricing tiers */
.pricing-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px,1fr)); gap: 10px; }
.pricing-tier {
    background: #16161F;
    border: 1px solid #1E1E2E;
    border-radius: 10px;
    padding: 16px 12px;
    text-align: center;
}
.tier-name  { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #6E6E8A; margin-bottom: 6px; }
.tier-price { font-family: 'Syne', sans-serif; font-size: 1.5rem; font-weight: 700; color: #E8E8F0; }
.tier-sales { font-size: 0.75rem; color: #6E6E8A; margin-top: 4px; }
.tier-rev   { font-size: 0.8rem; color: #4CAF82; margin-top: 4px; font-weight: 500; }

/* Schedule */
.schedule-row {
    display: grid;
    grid-template-columns: 90px 1fr 120px;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #1A1A24;
    align-items: start;
}
.sched-time  { font-size: 0.78rem; color: #6E6E8A; font-weight: 500; padding-top: 2px; }
.sched-title { font-size: 0.9rem; color: #E8E8F0; }
.sched-type  {
    font-size: 0.7rem; padding: 3px 10px; border-radius: 20px;
    background: #1A1A2E; color: #7B7BFF; border: 1px solid #2A2A4E;
    text-align: center;
}

/* Run button */
.stButton > button {
    background: linear-gradient(135deg, #5B5BFF, #FF6B6B) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.7rem 2rem !important;
    width: 100% !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Metric boxes */
.metric-row { display: flex; gap: 12px; margin-bottom: 1rem; flex-wrap: wrap; }
.metric-box {
    flex: 1; min-width: 120px;
    background: #111118;
    border: 1px solid #1E1E2E;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
}
.metric-val   { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700; color: #E8E8F0; }
.metric-label { font-size: 0.72rem; color: #6E6E8A; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 3px; }

/* Section divider */
.sec-divider {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #3A3A5A;
    margin: 1.5rem 0 0.8rem;
}

/* Status badges */
.badge-high   { color: #4CAF82; }
.badge-medium { color: #D4A84B; }
.badge-low    { color: #FF6B6B; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>EventForge AI</h1>
  <p>Multi-agent conference & event planning · powered by RAG + LangGraph</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar — inputs ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 Event Configuration")
    st.markdown("---")

    event_name = st.text_input(
        "Event Name",
        placeholder="e.g. IPL Fan Fest 2026",
        value="IPL Fan Fest 2026"
    )

    sport = st.selectbox(
        "Sport / Category",
        options=sorted(SUPPORTED_SPORTS),
        index=sorted(SUPPORTED_SPORTS).index("cricket"),
        help="Select a sport your data covers well"
    )

    geography = st.selectbox(
        "Geography",
        options=SUPPORTED_GEOGRAPHIES,
        index=SUPPORTED_GEOGRAPHIES.index("India"),
    )

    audience = st.slider(
        "Target Audience Size",
        min_value=500,
        max_value=100_000,
        value=50_000,
        step=500,
        format="%d"
    )

    budget = st.number_input(
        "Budget (USD)",
        min_value=0,
        max_value=10_000_000,
        value=500_000,
        step=50_000,
        format="%d"
    )

    notes = st.text_area(
        "Additional Notes (optional)",
        placeholder="e.g. Focus on youth engagement, outdoor venue preferred...",
        height=80
    )

    st.markdown("---")
    run_btn = st.button("⚡ Generate Event Plan", use_container_width=True)

# ── Main area ─────────────────────────────────────────────────────────────────

# Show placeholder when not yet run
if "state" not in st.session_state and not run_btn:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="result-card">
          <h3>🤖 How it works</h3>
          <p style="color:#6E6E8A;font-size:0.88rem;line-height:1.7">
            Configure your event in the sidebar, then hit <b style="color:#E8E8F0">Generate</b>.
            Six AI agents run in parallel — sponsors, speakers, venues, pricing, exhibitors, and GTM.
          </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="result-card">
          <h3>📊 Data-grounded</h3>
          <p style="color:#6E6E8A;font-size:0.88rem;line-height:1.7">
            Every recommendation is retrieved from your real dataset of 1,300+ events, 736 speakers,
            692 venues, and 102 known sponsors — not hallucinated.
          </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="result-card">
          <h3>⚡ Agents</h3>
          <p style="color:#6E6E8A;font-size:0.88rem;line-height:1.7">
            Sponsor · Speaker · Exhibitor · Venue · Pricing · Community · Ops · Synthesiser —
            all coordinated by a LangGraph orchestrator.
          </p>
        </div>
        """, unsafe_allow_html=True)

# ── Run pipeline ──────────────────────────────────────────────────────────────
if run_btn:
    # Validate
    try:
        clean = validate_and_normalise(sport, geography, audience, float(budget) if budget else None)
    except ValidationError as e:
        st.error(str(e))
        st.stop()

    # Progress UI
    progress_bar = st.progress(0)
    status       = st.status("🚀 Running agents...", expanded=True)

    agent_steps = [
        (15,  "🎯 Sponsor Agent — finding relevant sponsors..."),
        (30,  "🎤 Speaker Agent — discovering athletes & experts..."),
        (45,  "🏢 Exhibitor Agent — identifying exhibitors..."),
        (60,  "🏟️  Venue Agent — matching venues..."),
        (72,  "🎟️  Pricing Agent — modelling ticket tiers..."),
        (84,  "📣 Community Agent — building GTM strategy..."),
        (93,  "📋 Ops Agent — building event agenda..."),
        (100, "✨ Synthesiser — compiling final plan..."),
    ]

    with status:
        for pct, msg in agent_steps[:-1]:
            st.write(msg)
            progress_bar.progress(pct)
            time.sleep(0.4)

        st.write(agent_steps[-1][1])
        progress_bar.progress(99)

        final_name = event_name or f"{sport.title()} Event {geography} 2026"
        state = run_pipeline(
            event_category       = clean["event_category"],
            geography            = clean["geography"],
            target_audience_size = clean["target_audience_size"],
            budget_usd           = clean.get("budget_usd"),
            event_name           = final_name,
            additional_notes     = notes or None,
        )
        progress_bar.progress(100)

    st.session_state["state"]      = state
    st.session_state["event_name"] = final_name
    status.update(label="✅ Plan generated!", state="complete")


# ── Render results ─────────────────────────────────────────────────────────────
if "state" in st.session_state:
    state      = st.session_state["state"]
    event_name = st.session_state.get("event_name", "Your Event")

    sponsors    = state.get("sponsors")    or []
    speakers    = state.get("speakers")    or []
    venues      = state.get("venues")      or []
    pricing     = state.get("pricing")     or {}
    exhibitors  = state.get("exhibitors")  or []
    communities = state.get("communities") or {}
    ops_plan    = state.get("ops_plan")    or {}

    # ── Top metrics ──────────────────────────────────────────────────────────
    tiers = pricing.get("pricing_tiers", [])
    total_rev = pricing.get("total_revenue_projection_usd", 0)
    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box"><div class="metric-val">{len(sponsors)}</div><div class="metric-label">Sponsors</div></div>
      <div class="metric-box"><div class="metric-val">{len(speakers)}</div><div class="metric-label">Speakers</div></div>
      <div class="metric-box"><div class="metric-val">{len(venues)}</div><div class="metric-label">Venues</div></div>
      <div class="metric-box"><div class="metric-val">{len(exhibitors)}</div><div class="metric-label">Exhibitors</div></div>
      <div class="metric-box"><div class="metric-val">${total_rev:,.0f}</div><div class="metric-label">Rev Projection</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tabs = st.tabs(["🎯 Sponsors", "🎤 Speakers", "🏟️ Venues", "🎟️ Pricing",
                    "🏢 Exhibitors", "📣 GTM", "📋 Schedule", "📄 Full Report"])

    # ── SPONSORS ─────────────────────────────────────────────────────────────
    with tabs[0]:
        if sponsors:
            for s in sponsors:
                priority = s.get("priority", "Medium")
                badge_cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(priority, "badge-medium")
                st.markdown(f"""
                <div class="result-card">
                  <div style="display:flex;justify-content:space-between;align-items:start">
                    <div>
                      <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:700;color:#E8E8F0">{s.get('sponsor_name','—')}</div>
                      <div style="font-size:0.82rem;color:#6E6E8A;margin-top:3px">{s.get('sponsor_type','—')} · {s.get('estimated_deal_range','Negotiable')}</div>
                      <div style="font-size:0.83rem;color:#A0A0C0;margin-top:8px">{s.get('relevance_reason','')}</div>
                    </div>
                    <span class="{badge_cls}" style="font-size:0.78rem;font-weight:600;white-space:nowrap;padding-left:12px">{priority}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No sponsor data returned.")

    # ── SPEAKERS ──────────────────────────────────────────────────────────────
    with tabs[1]:
        if speakers:
            cols = st.columns(3)
            emojis = ["🎾","🏏","⚽","🏎️","🥊","🏀","🏒","⚾","🥋","⛳"]
            for i, s in enumerate(speakers):
                with cols[i % 3]:
                    emoji = emojis[i % len(emojis)]
                    st.markdown(f"""
                    <div class="speaker-item">
                      <div class="speaker-avatar">{emoji}</div>
                      <div class="speaker-name">{s.get('name','TBD')}</div>
                      <div class="speaker-sport">{s.get('sport_or_domain','')}</div>
                      <div class="speaker-tag">{s.get('suggested_session_type','')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No speaker data returned.")

    # ── VENUES ────────────────────────────────────────────────────────────────
    with tabs[2]:
        if venues:
            for i, v in enumerate(venues):
                rank_color = "#6BA3FF" if i == 0 else "#6E6E8A"
                st.markdown(f"""
                <div class="{'venue-top' if i==0 else 'result-card'}">
                  <div style="display:flex;justify-content:space-between">
                    <div>
                      <div class="venue-name">{v.get('venue_name','—')}</div>
                      <div class="venue-meta">
                        📍 {v.get('city','—')}, {v.get('country','—')} &nbsp;·&nbsp;
                        👥 Capacity: {v.get('capacity','—')} &nbsp;·&nbsp;
                        💰 {v.get('estimated_rental_range_usd','Contact venue')}
                      </div>
                      <div style="font-size:0.83rem;color:#A0A0C0;margin-top:8px">{v.get('recommendation_reason','')}</div>
                    </div>
                    <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:{rank_color};padding-left:12px">#{i+1}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No venue data returned.")

    # ── PRICING ───────────────────────────────────────────────────────────────
    with tabs[3]:
        if tiers:
            st.markdown('<div class="pricing-grid">', unsafe_allow_html=True)
            for t in tiers:
                st.markdown(f"""
                <div class="pricing-tier">
                  <div class="tier-name">{t.get('tier_name','—')}</div>
                  <div class="tier-price">${t.get('price_usd',0):,}</div>
                  <div class="tier-sales">{t.get('expected_sales',0):,} tickets</div>
                  <div class="tier-rev">+${t.get('revenue_est_usd',0):,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Attendance", f"{pricing.get('total_expected_attendance',0):,}")
            col2.metric("Revenue Projection", f"${pricing.get('total_revenue_projection_usd',0):,.0f}")
            col3.metric("Break-even Attendance", f"{pricing.get('break_even_attendance',0):,}")

            conf = pricing.get("confidence","—")
            st.markdown(f"**Model Confidence:** `{conf}`")
            st.caption(pricing.get("reasoning",""))
        else:
            st.info("No pricing data returned.")

    # ── EXHIBITORS ────────────────────────────────────────────────────────────
    with tabs[4]:
        if exhibitors:
            for e in exhibitors:
                st.markdown(f"""
                <div class="result-card" style="display:flex;justify-content:space-between;align-items:start">
                  <div>
                    <div style="font-weight:600;color:#E8E8F0">{e.get('company_name','—')}</div>
                    <div style="font-size:0.78rem;color:#6E6E8A;margin-top:3px">{e.get('category','—')} · {e.get('sub_category','—')} · {e.get('geography','—')}</div>
                    <div style="font-size:0.82rem;color:#A0A0C0;margin-top:6px">{e.get('why_good_fit','')}</div>
                  </div>
                  <span style="font-size:0.72rem;background:#1A1A2E;color:#7B7BFF;padding:4px 10px;border-radius:20px;white-space:nowrap;margin-left:12px;border:1px solid #2A2A4E">{e.get('booth_tier','Standard')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No exhibitor data returned.")

    # ── GTM ───────────────────────────────────────────────────────────────────
    with tabs[5]:
        gtm = communities.get("gtm_strategy", {})
        target_comms = communities.get("target_communities", [])

        if gtm:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Phase 1 — Pre-Event (8+ weeks)**")
                st.markdown(f"<p style='color:#A0A0C0;font-size:0.88rem'>{gtm.get('phase_1_pre_event','—')}</p>", unsafe_allow_html=True)
                st.markdown("**Phase 2 — Launch (4-8 weeks)**")
                st.markdown(f"<p style='color:#A0A0C0;font-size:0.88rem'>{gtm.get('phase_2_launch','—')}</p>", unsafe_allow_html=True)
            with col2:
                st.markdown("**Phase 3 — Final Push (0-4 weeks)**")
                st.markdown(f"<p style='color:#A0A0C0;font-size:0.88rem'>{gtm.get('phase_3_final_push','—')}</p>", unsafe_allow_html=True)
                st.markdown("**Key Channels**")
                channels = gtm.get("key_channels", [])
                st.markdown('<div class="pill-row">' + "".join(f'<span class="pill pill-silver">{c}</span>' for c in channels) + '</div>', unsafe_allow_html=True)
                st.markdown(f"<p style='color:#4CAF82;font-size:0.88rem;margin-top:8px'>Est. Reach: {gtm.get('estimated_reach',0):,}</p>", unsafe_allow_html=True)

        if target_comms:
            st.markdown("---")
            st.markdown("**Target Communities**")
            for c in target_comms:
                st.markdown(f"""
                <div class="result-card">
                  <div style="display:flex;justify-content:space-between">
                    <div>
                      <span style="font-weight:600;color:#E8E8F0">{c.get('community_name','—')}</span>
                      <span style="font-size:0.78rem;color:#6E6E8A;margin-left:10px">{c.get('platform','—')} · {c.get('members','—')} members</span>
                    </div>
                    <span style="font-size:0.75rem;color:#7B7BFF">{c.get('niche','—')}</span>
                  </div>
                  <div style="font-size:0.82rem;color:#A0A0C0;margin-top:6px;font-style:italic">"{c.get('outreach_message','')}"</div>
                </div>
                """, unsafe_allow_html=True)

    # ── SCHEDULE ──────────────────────────────────────────────────────────────
    with tabs[6]:
        agenda = ops_plan.get("agenda", [])
        if agenda:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            for item in agenda:
                st.markdown(f"""
                <div class="schedule-row">
                  <div class="sched-time">{item.get('time_slot','—')}</div>
                  <div>
                    <div class="sched-title">{item.get('session_title','—')}</div>
                    <div style="font-size:0.76rem;color:#6E6E8A;margin-top:2px">{item.get('speaker_or_performer','—')} · {item.get('room_or_stage','—')}</div>
                  </div>
                  <div class="sched-type">{item.get('session_type','—')}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            res = ops_plan.get("resource_plan", {})
            if res:
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("Rooms Needed", res.get("total_rooms_needed","—"))
                col2.metric("Staff Estimate", res.get("total_staff_est","—"))
                col3.markdown("**Equipment**")
                for item in res.get("equipment_checklist", []):
                    col3.markdown(f"- {item}")
        else:
            st.info("No schedule data returned.")

    # ── FULL REPORT ───────────────────────────────────────────────────────────
    with tabs[7]:
        final = state.get("final_plan","")
        if final:
            st.markdown(final)
            st.download_button(
                label="⬇️ Download Full Report (.md)",
                data=final.encode("utf-8"),
                file_name=f"{event_name.replace(' ','_')}_plan.md",
                mime="text/markdown",
            )
            debug = {k: v for k, v in state.items() if k not in ("messages","final_plan")}
            st.download_button(
                label="⬇️ Download Raw Agent Data (.json)",
                data=json.dumps(debug, indent=2, default=str, ensure_ascii=False).encode("utf-8"),
                file_name=f"{event_name.replace(' ','_')}_debug.json",
                mime="application/json",
            )
        else:
            st.info("No report generated.")

    if state.get("errors"):
        with st.expander("⚠️ Agent Warnings"):
            for e in state["errors"]:
                st.warning(e)
