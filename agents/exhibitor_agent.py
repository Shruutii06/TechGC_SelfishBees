"""Exhibitor Agent — FINAL (RAG + CSV fallback + SAFE)"""

import json, re
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from rag.retriever import query
from rag.csv_fallback import get_context
from agents.state import AgentState


SYSTEM_PROMPT = """You are the Exhibitor Agent.

Recommend real companies from the data.

Return JSON list:
- company_name
- category
- sub_category
- geography
- why_good_fit
- booth_tier

Return ONLY JSON.
"""


def run_exhibitor_agent(state: AgentState):
    print("\n===== EXHIBITOR AGENT START =====")

    inp = state["input"]
    sport = inp["event_category"]
    geo = inp["geography"]

    context = ""

    # ── SAFE RAG ─────────────────────────────
    try:
        raw = query("exhibitors", f"{sport} {geo}", n_results=5)
        context = get_context("exhibitors", raw, sport, geo)
        print("✅ Exhibitor RAG SUCCESS")

    except Exception as e:
        print("⚠️ Exhibitor RAG FAILED:", e)
        return {"exhibitors": []}   # ✅ prevent crash

    # If no data → skip LLM
    if not context.strip():
        print("❌ No exhibitor data found")
        return {"exhibitors": []}

    # ── LLM ─────────────────────────────
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=900   # increased — 400 caused JSON truncation
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name','TBD')}
Sport: {sport}
Geography: {geo}
Audience: {inp['target_audience_size']}

Exhibitors Database:
{context}

Recommend top exhibitors using ONLY real company names.
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

        # ── Truncation-safe JSON recovery ─────────────────────────────────────
        # If max_tokens cuts the response mid-JSON, recover any complete objects
        try:
            exhibitors = json.loads(text)
        except json.JSONDecodeError:
            # Find the last complete JSON object in the array
            last_brace = text.rfind("},")
            if last_brace == -1:
                last_brace = text.rfind("}")
            if last_brace != -1:
                recovered = text[:last_brace + 1].strip()
                # Wrap in array if needed
                if not recovered.startswith("["):
                    recovered = "[" + recovered
                recovered += "]"
                exhibitors = json.loads(recovered)
                print(f"⚠️ Recovered {len(exhibitors)} exhibitors from truncated JSON")
            else:
                raise

        if not isinstance(exhibitors, list):
            raise ValueError("Invalid exhibitor output")

        print(f"✅ EXHIBITORS GENERATED: {len(exhibitors)}")

    except Exception as e:
        print("❌ Exhibitor LLM ERROR:", e)
        exhibitors = []

    print("===== EXHIBITOR AGENT END =====\n")

    return {**state, "exhibitors": exhibitors}
