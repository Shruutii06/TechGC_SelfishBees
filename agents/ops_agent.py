"""
Event Ops / Execution Agent (Bonus — Highly Recommended)
Builds agenda, detects conflicts, and plans resources.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState

SYSTEM_PROMPT = """You are the Event Ops Agent for a multi-agent conference organizer system.

You receive the outputs of other agents (speakers, venues, sponsors) and produce:
1. A full event agenda / schedule
2. Conflict detection (overlapping sessions)
3. Resource allocation (rooms, speakers, timing)

Output a JSON object with:
- agenda: list of {
    time_slot, session_title, session_type,
    speaker_or_performer, room_or_stage, duration_minutes
  }
- conflicts_detected: list of strings describing any conflicts found
- resource_plan: {
    total_rooms_needed, total_staff_est,
    equipment_checklist: list of strings,
    logistics_notes: string
  }
- event_day_summary: string (2-3 sentence overview of the day)

Return ONLY valid JSON. No extra text."""


def run_ops_agent(state: AgentState) -> AgentState:
    inp = state["input"]
    speakers = state.get("speakers") or []
    venues   = state.get("venues") or []

    speaker_names = [s.get("name", "TBD") for s in speakers[:6]]
    top_venue = venues[0].get("venue_name", "TBD") if venues else "TBD"

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', inp['event_category'])}
Geography: {inp['geography']}
Audience Size: {inp['target_audience_size']}
Top Venue: {top_venue}

Confirmed Speakers/Performers:
{chr(10).join(f'- {n}' for n in speaker_names) or 'TBD'}

Build a full 1-day event agenda with session slots from 9 AM to 8 PM.
Include opening ceremony, 3-4 main sessions, networking breaks, and a closing.
"""),
    ]

    try:
        response = llm.invoke(messages)
        import json, re
        text = re.sub(r"^```(?:json)?|```$", "", response.content.strip(), flags=re.MULTILINE).strip()
        ops_plan = json.loads(text)
    except Exception as e:
        ops_plan = {}
        state.setdefault("errors", []).append(f"OpsAgent: {e}")

    return {**state, "ops_plan": ops_plan}
