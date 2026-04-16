"""Pricing Agent — FINAL (RAG + CSV fallback + SAFE)"""

import json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from rag.retriever import query
from rag.csv_fallback import get_context, attendance_fallback
from agents.state import AgentState


# ── Exact JSON schema the LLM MUST follow ──────────────────────────────────────
SYSTEM_PROMPT = """You are the Pricing & Footfall Agent.

Use the given pricing benchmarks and attendance data.

Return ONLY a raw JSON object with this EXACT structure (no markdown, no explanation):

{
  "pricing_tiers": [
    {
      "tier_name": "Budget",
      "price_usd": 25,
      "expected_sales": 20000,
      "revenue_est_usd": 500000
    },
    {
      "tier_name": "Premium Stand",
      "price_usd": 75,
      "expected_sales": 5000,
      "revenue_est_usd": 375000
    }
  ],
  "total_expected_attendance": 25000,
  "total_revenue_projection_usd": 875000,
  "break_even_attendance": 15000,
  "confidence": 0.8,
  "reasoning": "Brief explanation here."
}

RULES:
- pricing_tiers MUST be a JSON array (list), never a dict/object.
- Each tier MUST use exactly these keys: tier_name, price_usd, expected_sales, revenue_est_usd.
- All number values must be plain numbers (no $ signs, no commas).
- Return ONLY the JSON object. No markdown fences, no extra text.
"""


# ── Key alias map: normalize whatever the LLM returns to our expected keys ──────
TIER_KEY_ALIASES = {
    "tier_name":       ["tier_name", "name", "tier", "ticket_type", "category",
                        "level", "type", "label", "ticket_tier", "section"],
    "price_usd":       ["price_usd", "price", "cost", "amount", "ticket_price",
                        "price_per_ticket", "rate", "value", "usd", "fee"],
    "expected_sales":  ["expected_sales", "sales", "quantity", "tickets",
                        "expected_tickets", "units", "capacity", "count",
                        "estimated_sales", "attendance"],
    "revenue_est_usd": ["revenue_est_usd", "revenue", "revenue_est", "total_revenue",
                        "estimated_revenue", "rev", "income", "projected_revenue"],
}


def _normalize_tier(tier: dict) -> dict:
    """Map any LLM key aliases to canonical keys expected by app.py."""
    lower_tier = {k.lower(): v for k, v in tier.items()}
    result = {}

    for canonical, aliases in TIER_KEY_ALIASES.items():
        for alias in aliases:
            if alias in lower_tier:
                result[canonical] = lower_tier[alias]
                break

    # Clean price: strip "$", "," if it came back as a string
    if "price_usd" in result and isinstance(result["price_usd"], str):
        result["price_usd"] = float(re.sub(r"[^\d.]", "", result["price_usd"]) or 0)

    # Fallback tier_name if still missing
    if "tier_name" not in result:
        result["tier_name"] = next(iter(tier.values()), "—")

    return result


def _normalize_pricing_tiers(raw_tiers) -> list:
    """Convert whatever the LLM returns into a clean list of tier dicts."""
    if isinstance(raw_tiers, list):
        return [_normalize_tier(t) for t in raw_tiers if isinstance(t, dict)]

    if isinstance(raw_tiers, dict):
        normalized = []
        for key, val in raw_tiers.items():
            if isinstance(val, dict):
                val.setdefault("tier_name", key)
                normalized.append(_normalize_tier(val))
            else:
                # Scalar: {"Budget": 25} style
                normalized.append({"tier_name": key, "price_usd": val})
        return normalized

    return []


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
        max_tokens=800   # 400 was too low; caused truncation
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

Generate pricing model. Return ONLY the JSON object, no extra text.
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

        # Debug: print raw output so you can see what keys the LLM is actually using
        print("🔍 RAW PRICING JSON (first 400 chars):", text[:400])

        pricing = json.loads(text)

        if not isinstance(pricing, dict):
            raise ValueError("Invalid pricing output — expected dict")

        # ── Normalize tiers regardless of whatever keys the LLM chose ─────────
        raw_tiers = pricing.get("pricing_tiers", [])
        pricing["pricing_tiers"] = _normalize_pricing_tiers(raw_tiers)

        print(f"✅ PRICING GENERATED — {len(pricing['pricing_tiers'])} tiers: "
              f"{[t.get('tier_name') for t in pricing['pricing_tiers']]}")

    except Exception as e:
        print("❌ Pricing LLM ERROR:", e)
        pricing = {}

    print("===== PRICING AGENT END =====\n")

    return {**state, "pricing": pricing}
