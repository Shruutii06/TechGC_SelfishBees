"""
Event Ops / Execution Agent — FIXED
Bugs fixed:
  1. max_tokens=500 was too low for a full agenda JSON object → bumped to 1000
  2. No empty-response guard before json.loads → added explicit check
"""

import os, json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState


SYSTEM_PROMPT = """You are the Event Ops Agent.

Using the given speakers and venue, create a complete event execution plan.

Return a JSON object with exactly these fields:
- agenda: list of {
    time_slot, session_title, session_type,
    speaker_or_performer, room_or_stage, duration_minutes
  }
- conflicts_detected: list of strings
- resource_plan: {
    total_rooms_needed, total_staff_est,
    equipment_checklist: list,
    logistics_notes: string
  }
- event_day_summary: string

Return ONLY valid JSON. No markdown, no extra text.
"""

_FALLBACK_OPS = {
    "agenda": [
        {
            "time_slot": "09:00-10:00",
            "session_title": "Opening Ceremony",
            "session_type": "Ceremony",
            "speaker_or_performer": "TBD",
            "room_or_stage": "Main Stage",
            "duration_minutes": 60
        },
        {
            "time_slot": "10:00-11:30",
            "session_title": "Keynote Session",
            "session_type": "Keynote",
            "speaker_or_performer": "TBD",
            "room_or_stage": "Main Stage",
            "duration_minutes": 90
        },
        {
            "time_slot": "11:30-12:00",
            "session_title": "Networking Break",
            "session_type": "Break",
            "speaker_or_performer": "",
            "room_or_stage": "Lobby",
            "duration_minutes": 30
        },
        {
            "time_slot": "12:00-13:30",
            "session_title": "Panel Discussion",
            "session_type": "Panel",
            "speaker_or_performer": "TBD",
            "room_or_stage": "Main Stage",
            "duration_minutes": 90
        },
        {
            "time_slot": "13:30-14:30",
            "session_title": "Lunch Break",
            "session_type": "Break",
            "speaker_or_performer": "",
            "room_or_stage": "Dining Area",
            "duration_minutes": 60
        },
        {
            "time_slot": "14:30-16:00",
            "session_title": "Workshop / Demo Zone",
            "session_type": "Workshop",
            "speaker_or_performer": "TBD",
            "room_or_stage": "Hall B",
            "duration_minutes": 90
        },
        {
            "time_slot": "16:00-16:30",
            "session_title": "Afternoon Break",
            "session_type": "Break",
            "speaker_or_performer": "",
            "room_or_stage": "Lobby",
            "duration_minutes": 30
        },
        {
            "time_slot": "16:30-18:00",
            "session_title": "Closing Ceremony & Awards",
            "session_type": "Ceremony",
            "speaker_or_performer": "TBD",
            "room_or_stage": "Main Stage",
            "duration_minutes": 90
        }
    ],
    "conflicts_detected": [],
    "resource_plan": {
        "total_rooms_needed": 3,
        "total_staff_est": 50,
        "equipment_checklist": [
            "Main Stage", "LED Screen", "Sound System",
            "Lighting Rig", "Live Stream Setup",
            "Registration Kiosks", "Security Personnel"
        ],
        "logistics_notes": "Fallback plan — LLM generation failed. Please review and customise."
    },
    "event_day_summary": "Standard 1-day event structure (fallback). LLM generation did not succeed."
}


def run_ops_agent(state: AgentState) -> AgentState:
    print("\n===== OPS AGENT START =====")

    inp      = state["input"]
    speakers = state.get("speakers") or []
    venues   = state.get("venues") or []

    speaker_names = [s.get("name", "TBD") for s in speakers[:6]] or ["Guest Speaker TBD"]
    top_venue     = venues[0].get("venue_name", "Main Venue") if venues else "Main Venue"

    print("Speakers:", speaker_names)
    print("Venue:", top_venue)

    # FIX 1: 500 tokens cannot hold a full agenda + resource_plan JSON.
    #         Agenda alone (8 slots × 6 fields) ≈ 700 tokens → use 1000.
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.3,
        max_tokens=1000
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', inp['event_category'])}
Geography: {inp['geography']}
Audience: {inp['target_audience_size']}
Venue: {top_venue}

Speakers:
{chr(10).join(f"- {n}" for n in speaker_names)}

Create a full 1-day event plan (9 AM – 6 PM).
Include opening ceremony, 3 main sessions, breaks, closing ceremony.
Return ONLY a JSON object.
"""),
    ]

    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()

        # FIX 2: Guard against empty response before attempting json.loads
        if not raw_text:
            raise ValueError("LLM returned empty response")

        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()

        if not text:
            raise ValueError("Response was only markdown fences, no content")

        ops_plan = json.loads(text)

        if not isinstance(ops_plan, dict):
            raise ValueError(f"Expected dict, got {type(ops_plan)}")

        # Patch in real speaker/venue names into the fallback agenda slots if needed
        for slot in ops_plan.get("agenda", []):
            if slot.get("speaker_or_performer") in ("", "TBD", None) and speaker_names:
                slot["speaker_or_performer"] = speaker_names[0]

        print("✅ OPS PLAN GENERATED")

    except Exception as e:
        print("❌ OPS LLM ERROR:", e)
        ops_plan = _FALLBACK_OPS.copy()
        # Patch real names into the static fallback
        for slot in ops_plan["agenda"]:
            if slot["speaker_or_performer"] == "TBD" and speaker_names:
                slot["speaker_or_performer"] = speaker_names[0]
                break
        for slot in ops_plan["agenda"]:
            if slot["room_or_stage"] == "Main Stage":
                slot["room_or_stage"] = top_venue

    print("===== OPS AGENT END =====\n")
    return {**state, "ops_plan": ops_plan}
