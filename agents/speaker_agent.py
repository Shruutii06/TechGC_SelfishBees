"""
Speaker / Artist Agent
Discovers and recommends speakers, athletes, or subject matter experts.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query, format_results
from agents.state import AgentState

SYSTEM_PROMPT = """You are the Speaker/Artist Agent for a multi-agent conference organizer system.

Your job is to recommend the BEST speakers, athletes, or subject matter experts for an event, based on:
- Relevance to the event topic/sport
- Past speaking or performance experience
- Influence (followers, publications, achievements)
- Geographic accessibility

You will be given:
1. Event details
2. Relevant speaker/athlete data from a database

Output a structured JSON list with these fields:
- name
- sport_or_domain
- nationality
- why_recommended (1-2 sentences)
- influence_level (High / Medium / Emerging)
- suggested_session_type (Keynote / Panel / Workshop / Performance / Opening Ceremony)

Return ONLY valid JSON — a list of speaker objects. No extra text."""


def run_speaker_agent(state: AgentState) -> AgentState:
    inp = state["input"]
    query_text = f"{inp['event_category']} speakers experts {inp['geography']}"

    raw = query("speakers", query_text, n_results=12)
    context = format_results(raw, max_items=12)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event Details:
- Category: {inp['event_category']}
- Geography: {inp['geography']}
- Target Audience Size: {inp['target_audience_size']}
- Event Name: {inp.get('event_name', 'TBD')}
- Notes: {inp.get('additional_notes', 'None')}

Speakers/Athletes from Database:
{context}

Recommend the top 8 speakers or featured athletes/artists for this event.
Also suggest an agenda topic for each speaker.
"""),
    ]

    try:
        response = llm.invoke(messages)
        import json, re
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        speakers = json.loads(text)
    except Exception as e:
        speakers = []
        state.setdefault("errors", []).append(f"SpeakerAgent: {e}")

    return {**state, "speakers": speakers}
