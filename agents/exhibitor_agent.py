"""
Exhibitor Agent — identifies companies to exhibit at the event
"""

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query, format_results
from agents.state import AgentState

SYSTEM_PROMPT = """You are the Exhibitor Agent for a multi-agent conference organizer system.

Recommend companies that should exhibit at this event. Cluster them by:
- startup / enterprise / tools / individual / NGO

Output a JSON list with fields:
- company_name
- category (startup / enterprise / tools / individual / NGO)
- sub_category (e.g. Wearables, Analytics, Broadcasting)
- geography
- why_good_fit (1 sentence)
- booth_tier (Premium / Standard / Startup Booth)

Return ONLY valid JSON. No extra text."""


def run_exhibitor_agent(state: AgentState) -> AgentState:
    inp = state["input"]
    raw = query("exhibitors", f"{inp['event_category']} {inp['geography']}", n_results=10)
    context = format_results(raw, max_items=10)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', inp['event_category'])}
Geography: {inp['geography']}
Audience Size: {inp['target_audience_size']}

Exhibitors Database:
{context}

Recommend top 8 exhibitors, clustered by category.
"""),
    ]

    try:
        response = llm.invoke(messages)
        import json, re
        text = re.sub(r"^```(?:json)?|```$", "", response.content.strip(), flags=re.MULTILINE).strip()
        exhibitors = json.loads(text)
    except Exception as e:
        exhibitors = []
        state.setdefault("errors", []).append(f"ExhibitorAgent: {e}")

    return {**state, "exhibitors": exhibitors}
