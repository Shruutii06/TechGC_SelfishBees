"""
Venue Agent — FIXED
Bugs fixed:
  1. max_tokens=400 truncated JSON mid-string at line 45 → bumped to 900
  2. No empty-response guard before json.loads → added explicit check
"""

import json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from rag.retriever import query
from rag.csv_fallback import get_context
from agents.state import AgentState


SYSTEM_PROMPT = """You are the Venue Agent.

Recommend REAL venues only from provided data.

Return a JSON list. Each item has exactly these fields:
- venue_name
- city
- country
- capacity
- sport_suitability
- estimated_rental_range_usd
- recommendation_reason
- rank

Return ONLY valid JSON. No markdown, no extra text.
"""


def safe_json_parse(text: str):
    if not text or not text.strip():
        return None

    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    # Last-resort: extract first [...] or {...} block
    match = re.search(r"\[.*\]|\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return None


def run_venue_agent(state: AgentState):
    print("\n===== VENUE AGENT START =====")

    inp = state["input"]
    sport = inp["event_category"]
    geo   = inp["geography"]

    # ── SAFE RAG ─────────────────────────────
    try:
        raw = query("venues", f"{sport} venue {geo}", n_results=5)
        context = get_context("venues", raw, sport, geo)
        print("✅ Venue RAG SUCCESS")
    except Exception as e:
        print("⚠️ Venue RAG FAILED:", e)
        return {**state, "venues": []}

    if not context.strip():
        print("❌ No venue data")
        return {**state, "venues": []}

    # FIX 1: 400 tokens is far too low for 5 venue objects × 8 fields.
    #         5 venues × ~150 tokens each ≈ 750 tokens → use 1000.
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=1000
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', 'TBD')}
Sport: {sport}
Geography: {geo}
Expected Attendance: {inp['target_audience_size']}

Venues Database:
{context}

Pick top 5 venues. Return ONLY a JSON list.
"""),
    ]

    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()

        # FIX 2: Guard against empty response
        if not raw_text:
            raise ValueError("LLM returned empty response")

        venues = safe_json_parse(raw_text)

        if not isinstance(venues, list):
            raise ValueError(f"Expected list, got {type(venues)}: {raw_text[:200]}")

        print(f"✅ VENUES GENERATED: {len(venues)}")

    except Exception as e:
        print("❌ Venue LLM ERROR:", e)
        venues = []

    print("===== VENUE AGENT END =====\n")
    return {**state, "venues": venues}
