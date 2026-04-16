"""
Community Agent — FIXED
Bugs fixed:
  1. max_tokens=400 truncated JSON at char 1429 (line 50) → bumped to 1000
     target_communities (list) + gtm_strategy (dict with multiple keys) easily
     exceeds 600-800 tokens; 1000 gives comfortable headroom.
  2. No empty-response guard before json.loads → added explicit check
  3. re.MULTILINE flag added to markdown-strip regex for reliable fence removal
  4. Return value on RAG failure was {"communities": {}} without spreading state
     → fixed to {**state, "communities": {}} to avoid dropping other agent outputs
"""

import json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from rag.retriever import query, format_results
from agents.state import AgentState


SYSTEM_PROMPT = """You are the Community & GTM Agent.

Return a JSON object with exactly these two keys:
- target_communities: list of objects, each with:
    - community_name
    - platform
    - niche
    - estimated_reach
    - engagement_tactic
- gtm_strategy: object with:
    - channels: list of strings
    - key_messages: list of strings
    - influencer_approach: string
    - timeline_weeks: number

Return ONLY valid JSON. No markdown, no extra text.
"""


def run_community_agent(state: AgentState):
    print("\n===== COMMUNITY AGENT START =====")

    inp = state["input"]

    # ── SAFE RAG ─────────────────────────────
    try:
        raw = query(
            "communities",
            f"{inp['event_category']} community {inp['geography']}",
            n_results=5
        )
        context = format_results(raw, max_items=10)
        print("✅ Community RAG SUCCESS")

    except Exception as e:
        print("⚠️ Community RAG FAILED:", e)
        # FIX 4: spread state so other agent outputs are not dropped
        return {**state, "communities": {}}

    if not context.strip():
        print("❌ No community data")
        return {**state, "communities": {}}

    # FIX 1: 400 tokens cannot fit target_communities list + gtm_strategy dict.
    #         Typical output ≈ 700-900 tokens → use 1000.
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        max_tokens=1000
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', 'TBD')}
Category: {inp['event_category']}
Geography: {inp['geography']}

Communities Database:
{context}

Build GTM plan. Return ONLY a JSON object.
"""),
    ]

    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()

        # FIX 2: Guard against empty response before attempting json.loads
        if not raw_text:
            raise ValueError("LLM returned empty response")

        # FIX 3: re.MULTILINE so ^ and $ match line boundaries reliably
        text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw_text,
            flags=re.MULTILINE
        ).strip()

        if not text:
            raise ValueError("Response was only markdown fences, no content")

        communities = json.loads(text)

        if not isinstance(communities, dict):
            raise ValueError(f"Expected dict, got {type(communities)}")

        print("✅ COMMUNITY PLAN GENERATED")

    except Exception as e:
        print("❌ Community LLM ERROR:", e)
        communities = {}

    print("===== COMMUNITY AGENT END =====\n")

    return {**state, "communities": communities}
