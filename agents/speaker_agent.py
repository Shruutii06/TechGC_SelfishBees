"""
Speaker Agent — FIXED
Bugs fixed:
  1. max_tokens=400 was too low for a 5-item JSON list with 8 fields → bumped to 900
  2. No guard for empty LLM response → added explicit empty-string check before json.loads
  3. Reduced to 6 fields to stay within token budget
"""

import os, json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query
from rag.csv_fallback import get_context
from agents.state import AgentState


SYSTEM_PROMPT = """You are the Speaker Agent.

Use ONLY real names from the data provided.

Return a JSON list. Each item has exactly these fields:
- name
- sport_or_domain
- nationality
- role
- why_recommended
- influence_level

Return ONLY valid JSON. No markdown, no extra text.
"""


def run_speaker_agent(state: AgentState) -> AgentState:
    print("\n===== SPEAKER AGENT START =====")

    inp = state["input"]
    sport, geo = inp["event_category"], inp["geography"]

    # ── RAG ─────────────────────────
    try:
        raw = query("speakers", f"{sport} speakers {geo}", n_results=5)
        context = get_context("speakers", raw, sport, geo)
        print("✅ RAG SUCCESS")
    except Exception as e:
        print("❌ RAG FAILED:", e)
        context = ""

    if not context.strip():
        print("❌ No speaker data — skipping LLM")
        return {**state, "speakers": []}

    # ── LLM ─────────────────────────
    # FIX 1: 400 tokens cannot fit 5 objects × 8 fields.
    #         6 fields × 5 speakers ≈ 600-800 tokens → use 900 to be safe.
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2, max_tokens=900)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', 'TBD')}
Sport: {sport}
Geo: {geo}

DATA:
{context}

Pick 5 speakers from above. Return ONLY a JSON list.
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

        speakers = json.loads(text)

        if not isinstance(speakers, list):
            raise ValueError(f"Expected list, got {type(speakers)}")

        print(f"✅ SPEAKERS GENERATED: {len(speakers)}")

    except Exception as e:
        print("❌ LLM ERROR:", e)
        speakers = []

    print("===== SPEAKER AGENT END =====\n")
    return {**state, "speakers": speakers}
