"""
Sponsor Agent — FIXED
Bugs fixed:
  1. max_tokens=400 truncated the JSON list mid-string at line 33 → bumped to 1000
  2. No empty-response guard before json.loads → added explicit check
  3. re.MULTILINE flag was missing on the markdown-strip regex → added
"""

import os, json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query, format_results
from rag.csv_fallback import get_context
from agents.state import AgentState


SYSTEM_PROMPT = """You are the Sponsor Agent for a multi-agent conference organizer system.

Recommend the BEST real sponsors from the data provided. Use actual brand names from the database.

Return a JSON list. Each item has exactly these fields:
- sponsor_name
- sponsor_type
- relevance_reason
- estimated_deal_range
- priority

Return ONLY valid JSON — a list. No markdown, no extra text."""


def run_sponsor_agent(state: AgentState) -> AgentState:
    print("\n===== SPONSOR AGENT START =====")

    inp = state["input"]
    sport, geo = inp["event_category"], inp["geography"]

    # ── RAG ─────────────────────────────
    try:
        raw = query("sponsors", f"{sport} sponsors {geo}", n_results=5)
        context = get_context("sponsors", raw, sport, geo)
        print("✅ Sponsor RAG SUCCESS")
    except Exception as e:
        print("⚠️ Sponsor RAG FAILED:", e)
        return {**state, "sponsors": []}

    try:
        event_raw = query("events", f"{sport} {geo}", n_results=5)
        event_ctx = format_results(event_raw, max_items=5)
    except Exception:
        event_ctx = ""

    # FIX 1: 400 tokens cannot fit 8 sponsor objects × 5 fields.
    #         8 sponsors × ~120 tokens each ≈ 960 → use 1000.
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=1000)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', 'TBD')} | Sport: {sport} | Geography: {geo}
Audience: {inp['target_audience_size']} | Budget: {inp.get('budget_usd', 'Not specified')} USD

Sponsors Database:
{context}

Similar Events:
{event_ctx}

Recommend top 8 sponsors. Use real brand names from the database above.
Return ONLY a JSON list.
"""),
    ]

    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()

        # FIX 2: Guard against empty response before attempting json.loads
        if not raw_text:
            raise ValueError("LLM returned empty response")

        # FIX 3: re.MULTILINE so ^ and $ match start/end of each line
        text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw_text,
            flags=re.MULTILINE
        ).strip()

        if not text:
            raise ValueError("Response was only markdown fences, no content")

        sponsors = json.loads(text)

        if not isinstance(sponsors, list):
            raise ValueError(f"Expected list, got {type(sponsors)}")

        print(f"✅ SPONSORS GENERATED: {len(sponsors)}")

    except Exception as e:
        print("❌ Sponsor LLM ERROR:", e)
        sponsors = []
        state.setdefault("errors", []).append(f"SponsorAgent: {e}")

    print("===== SPONSOR AGENT END =====\n")
    return {**state, "sponsors": sponsors}
