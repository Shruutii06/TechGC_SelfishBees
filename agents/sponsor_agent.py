"""
Sponsor Agent
Recommends and prioritises potential sponsors for a given event.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query, format_results
from agents.state import AgentState

SYSTEM_PROMPT = """You are the Sponsor Agent for a multi-agent conference organizer system.

Your job is to recommend the BEST potential sponsors for a new event, based on:
- Industry relevance to the event category
- Geographic alignment
- Historical sponsorship frequency
- Deal size / sponsor tier

You will be given:
1. The event details (category, geography, audience size)
2. Relevant sponsor data retrieved from a database

Output a structured JSON list of recommended sponsors with these fields:
- sponsor_name
- sponsor_type (e.g. Title, Gold, Silver, Official Apparel, Tech Partner)
- relevance_reason (1-2 sentences)
- estimated_deal_range (if known, else "Negotiable")
- priority (High / Medium / Low)

Return ONLY valid JSON — a list of sponsor objects. No extra text."""


def run_sponsor_agent(state: AgentState) -> AgentState:
    inp = state["input"]
    query_text = f"{inp['event_category']} sponsors {inp['geography']}"

    # RAG retrieval
    raw = query("sponsors", query_text, n_results=10)
    context = format_results(raw, max_items=10)

    # Also pull relevant events for additional context
    event_raw = query("events", f"{inp['event_category']} {inp['geography']}", n_results=5)
    event_context = format_results(event_raw, max_items=5)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event Details:
- Category: {inp['event_category']}
- Geography: {inp['geography']}
- Target Audience Size: {inp['target_audience_size']}
- Budget: {inp.get('budget_usd', 'Not specified')} USD
- Event Name: {inp.get('event_name', 'TBD')}

Known Sponsors from Database:
{context}

Similar Events for Context:
{event_context}

Recommend the top 8 sponsors for this event.
"""),
    ]

    try:
        response = llm.invoke(messages)
        import json, re
        text = response.content.strip()
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        sponsors = json.loads(text)
    except Exception as e:
        sponsors = []
        state.setdefault("errors", []).append(f"SponsorAgent: {e}")

    return {**state, "sponsors": sponsors}
