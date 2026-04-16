"""Pricing Agent — FINAL (RAG + CSV fallback + SAFE)"""

import json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from rag.retriever import query
from rag.csv_fallback import get_context, attendance_fallback
from agents.state import AgentState


SYSTEM_PROMPT = """You are the Pricing & Footfall Agent.

Use the given pricing benchmarks and attendance data.

Return JSON:
- pricing_tiers
- total_expected_attendance
- total_revenue_projection_usd
- break_even_attendance
- confidence
- reasoning

Return ONLY JSON.
"""


def run_pricing_agent(state: AgentState):
    print("\n===== PRICING AGENT START =====")

    inp = state["input"]
    sport = inp["event_category"]
    geo = inp["geography"]

    context = ""

    # ── SAFE RAG ─────────────────────────────
    try:
        raw = query("ticket_pricing", f"{sport} {geo} ticket price attendance", n_results=5)
        context = get_context("ticket_pricing", raw, sport, geo)
        print("✅ Pricing RAG SUCCESS")

    except Exception as e:
        print("⚠️ Pricing RAG FAILED:", e)
        context = ""

    # Attendance fallback always works
    att_ctx = attendance_fallback(sport)

    # If BOTH empty → return safely
    if not context.strip() and not att_ctx.strip():
        print("❌ No pricing data available")
        return {"pricing": {}}

    # ── LLM ─────────────────────────────
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=400   # ✅ prevent rate limit blowups
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name','TBD')}
Sport: {sport}
Geography: {geo}
Target Audience: {inp['target_audience_size']}
Budget: {inp.get('budget_usd','Not specified')} USD

Ticket Pricing Benchmarks:
{context}

Historical Attendance Data:
{att_ctx}

Generate pricing model.
"""),
    ]

    try:
        response = llm.invoke(messages)

        text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response.content.strip(),
            flags=re.MULTILINE
        ).strip()

        pricing = json.loads(text)

        if not isinstance(pricing, dict):
            raise ValueError("Invalid pricing output")

        print("✅ PRICING GENERATED")

    except Exception as e:
        print("❌ Pricing LLM ERROR:", e)
        pricing = {}

    print("===== PRICING AGENT END =====\n")

    return {**state, "pricing": pricing}