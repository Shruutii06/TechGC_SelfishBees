"""
Master Orchestrator — LangGraph Multi-Agent Pipeline
Runs all 6 agents in parallel where possible, then synthesises results.

Graph structure:
    START
      │
      ├──► SponsorAgent   ─┐
      ├──► SpeakerAgent   ─┤
      ├──► ExhibitorAgent ─┼──► OpsAgent ──► FinalSynthesiser ──► END
      ├──► VenueAgent     ─┤
      ├──► PricingAgent   ─┘
      └──► CommunityAgent ─┘
"""

from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json

from agents.state import AgentState, ConferenceInput
from agents.sponsor_agent   import run_sponsor_agent
from agents.speaker_agent   import run_speaker_agent
from agents.exhibitor_agent import run_exhibitor_agent
from agents.venue_agent     import run_venue_agent
from agents.pricing_agent   import run_pricing_agent
from agents.community_agent import run_community_agent
from agents.ops_agent       import run_ops_agent


# ── Final Synthesiser ────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """You are the Master Conference Organizer AI.

You have received outputs from 7 specialised agents. Synthesise everything into a
clean, professional Conference Planning Report with these sections:

1. Executive Summary (3-4 sentences)
2. Recommended Sponsors (top 5, with tier)
3. Featured Speakers / Performers (top 5, with session type)
4. Exhibitor Lineup (by category)
5. Venue Recommendation (top choice with reason)
6. Ticket Pricing Model (tiers + revenue projection)
7. GTM & Community Strategy (key channels + phases)
8. Event Day Schedule (key time slots)
9. Resource & Ops Plan
10. Risk Flags (any conflicts or gaps detected)

Be specific, actionable, and concise. Format as a clean markdown report."""


def run_synthesiser(state: AgentState) -> AgentState:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)

    summary_data = {
        "event_input":  state["input"],
        "sponsors":     state.get("sponsors", []),
        "speakers":     state.get("speakers", []),
        "exhibitors":   state.get("exhibitors", []),
        "venues":       state.get("venues", []),
        "pricing":      state.get("pricing", {}),
        "communities":  state.get("communities", {}),
        "ops_plan":     state.get("ops_plan", {}),
        "errors":       state.get("errors", []),
    }

    messages = [
        SystemMessage(content=SYNTHESIS_PROMPT),
        HumanMessage(content=f"Here is all agent output:\n\n{json.dumps(summary_data, indent=2)}"),
    ]

    try:
        response = llm.invoke(messages)
        final_plan = response.content
    except Exception as e:
        final_plan = f"Synthesis failed: {e}"

    return {**state, "final_plan": final_plan}


# ── Build Graph ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    # Add all agent nodes
    g.add_node("sponsor_agent",   run_sponsor_agent)
    g.add_node("speaker_agent",   run_speaker_agent)
    g.add_node("exhibitor_agent", run_exhibitor_agent)
    g.add_node("venue_agent",     run_venue_agent)
    g.add_node("pricing_agent",   run_pricing_agent)
    g.add_node("community_agent", run_community_agent)
    g.add_node("ops_agent",       run_ops_agent)
    g.add_node("synthesiser",     run_synthesiser)

    # All specialist agents run from START in parallel
    g.set_entry_point("sponsor_agent")   # LangGraph fans out from here

    # Parallel execution: all agents → ops_agent
    for agent in ["sponsor_agent", "speaker_agent", "exhibitor_agent",
                  "venue_agent", "pricing_agent", "community_agent"]:
        g.add_edge(agent, "ops_agent")

    # Ops agent uses speaker + venue outputs → synthesiser
    g.add_edge("ops_agent", "synthesiser")
    g.add_edge("synthesiser", END)

    return g.compile()


# ── Public API ───────────────────────────────────────────────────────────────

def run_pipeline(
    event_category:       str,
    geography:            str,
    target_audience_size: int,
    budget_usd:           float | None = None,
    event_name:           str | None   = None,
    additional_notes:     str | None   = None,
) -> AgentState:
    """
    Run the full multi-agent pipeline.

    Returns the final AgentState including `final_plan` (markdown report)
    and all individual agent outputs.
    """
    graph = build_graph()

    initial_state: AgentState = {
        "input": {
            "event_category":        event_category,
            "geography":             geography,
            "target_audience_size":  target_audience_size,
            "budget_usd":            budget_usd,
            "event_name":            event_name,
            "additional_notes":      additional_notes,
        },
        "sponsors":    None,
        "speakers":    None,
        "exhibitors":  None,
        "venues":      None,
        "pricing":     None,
        "communities": None,
        "ops_plan":    None,
        "final_plan":  None,
        "errors":      [],
        "messages":    [],
    }

    return graph.invoke(initial_state)
