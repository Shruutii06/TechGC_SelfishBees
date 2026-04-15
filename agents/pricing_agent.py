"""
Pricing & Footfall Agent
Predicts optimal ticket pricing and expected attendance.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query, format_results
from agents.state import AgentState

SYSTEM_PROMPT = """You are the Pricing & Footfall Agent for a multi-agent conference organizer system.

Your job:
1. Predict optimal ticket pricing tiers
2. Estimate expected attendance
3. Model the relationship between price and conversion
4. Project revenue and break-even

Use historical event data provided to benchmark your predictions.

Output a single JSON object with:
- pricing_tiers: list of {tier_name, price_usd, expected_sales, revenue_est_usd}
  (tiers: Early Bird, Standard, VIP, Online/Virtual)
- total_expected_attendance: int
- total_revenue_projection_usd: float
- break_even_attendance: int (rough estimate)
- confidence: High / Medium / Low
- reasoning: 2-3 sentences explaining the model

Return ONLY valid JSON. No extra text."""


def run_pricing_agent(state: AgentState) -> AgentState:
    inp = state["input"]
    raw = query("ticket_pricing",
                f"{inp['event_category']} {inp['geography']} ticket price attendance",
                n_results=10)
    context = format_results(raw, max_items=10)

    # Also pull Olympics data for large-scale benchmarks
    olym = query("olympics", f"attendance athletes {inp['geography']}", n_results=3)
    olym_ctx = format_results(olym, max_items=3)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', inp['event_category'])}
Geography: {inp['geography']}
Target Audience Size: {inp['target_audience_size']}
Budget: {inp.get('budget_usd', 'Not specified')} USD

Historical Pricing Benchmarks:
{context}

Large-Scale Event Reference:
{olym_ctx}

Generate the pricing model.
"""),
    ]

    try:
        response = llm.invoke(messages)
        import json, re
        text = re.sub(r"^```(?:json)?|```$", "", response.content.strip(), flags=re.MULTILINE).strip()
        pricing = json.loads(text)
    except Exception as e:
        pricing = {}
        state.setdefault("errors", []).append(f"PricingAgent: {e}")

    return {**state, "pricing": pricing}
