"""
Master Orchestrator — FINAL (SEQUENTIAL, NO TOKEN SPIKES)
"""

from langgraph.graph import StateGraph, END
import json
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from agents.state import AgentState
from agents.sponsor_agent   import run_sponsor_agent
from agents.speaker_agent   import run_speaker_agent
from agents.exhibitor_agent import run_exhibitor_agent
from agents.venue_agent     import run_venue_agent
from agents.pricing_agent   import run_pricing_agent
from agents.community_agent import run_community_agent
from agents.ops_agent       import run_ops_agent


# ── FINAL SYNTHESIS ─────────────────────────────────────────────

SYNTHESIS_PROMPT = """You are the Master Conference Organizer AI.

Create a clean markdown report with:
1. Executive Summary
2. Sponsors
3. Speakers
4. Exhibitors
5. Venue
6. Pricing
7. GTM Strategy
8. Schedule
9. Ops Plan
10. Risks
"""

def run_synthesiser(state: AgentState) -> AgentState:
    print("\n===== SYNTHESIS START =====")

    llm = ChatGroq(
        model="llama-3.1-8b-instant",  # cheaper + faster
        temperature=0.3,
        max_tokens=800
    )

    summary_data = {
        "input": state["input"],
        "sponsors": state.get("sponsors", []),
        "speakers": state.get("speakers", []),
        "exhibitors": state.get("exhibitors", []),
        "venues": state.get("venues", []),
        "pricing": state.get("pricing", {}),
        "communities": state.get("communities", {}),
        "ops_plan": state.get("ops_plan", {}),
        "errors": state.get("errors", []),
    }

    try:
        response = llm.invoke([
            SystemMessage(content=SYNTHESIS_PROMPT),
            HumanMessage(content=json.dumps(summary_data, indent=2))
        ])

        print("✅ SYNTHESIS COMPLETE")
        return {**state, "final_plan": response.content}

    except Exception as e:
        print(f"❌ SYNTHESIS ERROR: {e}")
        return {**state, "final_plan": f"Synthesis failed: {e}"}


# ── BUILD GRAPH (SEQUENTIAL) ────────────────────────────────────

def build_graph():
    g = StateGraph(AgentState)

    # Nodes
    g.add_node("sponsor", run_sponsor_agent)
    g.add_node("speaker", run_speaker_agent)
    g.add_node("exhibitor", run_exhibitor_agent)
    g.add_node("venue", run_venue_agent)
    g.add_node("pricing", run_pricing_agent)
    g.add_node("community", run_community_agent)
    g.add_node("ops", run_ops_agent)
    g.add_node("synth", run_synthesiser)

    # Entry
    g.set_entry_point("sponsor")

    # 🔥 SEQUENTIAL FLOW (IMPORTANT FIX)
    g.add_edge("sponsor", "speaker")
    g.add_edge("speaker", "exhibitor")
    g.add_edge("exhibitor", "venue")
    g.add_edge("venue", "pricing")
    g.add_edge("pricing", "community")
    g.add_edge("community", "ops")
    g.add_edge("ops", "synth")
    g.add_edge("synth", END)

    return g.compile()


# ── RUN PIPELINE ────────────────────────────────────────────────

def run_pipeline(**kwargs) -> AgentState:
    graph = build_graph()

    state: AgentState = {
        "input": kwargs,
        "sponsors": None,
        "speakers": None,
        "exhibitors": None,
        "venues": None,
        "pricing": None,
        "communities": None,
        "ops_plan": None,
        "final_plan": None,
        "errors": [],
        "messages": [],
    }

    return graph.invoke(state)