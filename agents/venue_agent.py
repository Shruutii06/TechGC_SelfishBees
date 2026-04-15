"""
Venue Agent — recommends venues based on city, footfall, and budget
"""

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query, format_results
from agents.state import AgentState

SYSTEM_PROMPT = """You are the Venue Agent for a multi-agent conference organizer system.

Recommend the best venues for this event based on:
- City / geography match
- Capacity vs expected footfall
- Budget constraints
- Sport or event type suitability
- Past event usage

Output a JSON list with fields:
- venue_name
- city
- country
- capacity
- sport_suitability
- estimated_rental_range_usd (if known, else "Contact venue")
- past_events_note (if known)
- recommendation_reason (1-2 sentences)
- rank (1 = best fit)

Return ONLY valid JSON. No extra text."""


def run_venue_agent(state: AgentState) -> AgentState:
    inp = state["input"]
    raw = query("venues", f"{inp['event_category']} venue {inp['geography']}", n_results=10)
    context = format_results(raw, max_items=10)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', inp['event_category'])}
Geography: {inp['geography']}
Expected Attendance: {inp['target_audience_size']}
Budget: {inp.get('budget_usd', 'Not specified')} USD

Venues Database:
{context}

Recommend top 5 venues, ranked by fit.
"""),
    ]

    try:
        response = llm.invoke(messages)
        import json, re
        text = re.sub(r"^```(?:json)?|```$", "", response.content.strip(), flags=re.MULTILINE).strip()
        venues = json.loads(text)
    except Exception as e:
        venues = []
        state.setdefault("errors", []).append(f"VenueAgent: {e}")

    return {**state, "venues": venues}
