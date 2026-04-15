"""
Community & GTM Agent
Identifies relevant communities and creates a distribution/promotion plan.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from rag.retriever import query, format_results
from agents.state import AgentState

SYSTEM_PROMPT = """You are the Community & GTM (Go-To-Market) Agent for a multi-agent conference organizer system.

Your job:
1. Identify the most relevant communities to promote the event (Discord, Reddit, LinkedIn, Slack, Facebook Groups)
2. Categorise communities by niche
3. Create a GTM distribution plan with messaging strategy

Output a JSON object with:
- target_communities: list of {
    community_name, platform, niche, members, why_relevant,
    outreach_message (short 2-sentence pitch for that community)
  }
- gtm_strategy: {
    phase_1_pre_event: string (what to do 8+ weeks out),
    phase_2_launch: string (4-8 weeks out),
    phase_3_final_push: string (0-4 weeks out),
    key_channels: list of strings,
    estimated_reach: int
  }

Return ONLY valid JSON. No extra text."""


def run_community_agent(state: AgentState) -> AgentState:
    inp = state["input"]
    raw = query("communities",
                f"{inp['event_category']} community {inp['geography']}",
                n_results=10)
    context = format_results(raw, max_items=10)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Event: {inp.get('event_name', inp['event_category'])}
Category: {inp['event_category']}
Geography: {inp['geography']}
Target Audience Size: {inp['target_audience_size']}
Notes: {inp.get('additional_notes', 'None')}

Communities Database:
{context}

Build the GTM plan and identify top 6 communities to target.
"""),
    ]

    try:
        response = llm.invoke(messages)
        import json, re
        text = re.sub(r"^```(?:json)?|```$", "", response.content.strip(), flags=re.MULTILINE).strip()
        communities = json.loads(text)
    except Exception as e:
        communities = {}
        state.setdefault("errors", []).append(f"CommunityAgent: {e}")

    return {**state, "communities": communities}
