"""
Shared State Schema for the Multi-Agent Conference Organizer
All agents read from and write to this state object.
"""

from typing import TypedDict, Optional, Any


class ConferenceInput(TypedDict):
    """Input provided by the user to kick off the system."""
    event_category: str        # e.g. "AI Conference", "Sports", "Music Festival"
    geography: str             # e.g. "India", "Europe", "USA", "Singapore"
    target_audience_size: int  # e.g. 5000
    budget_usd: Optional[float]
    event_name: Optional[str]
    additional_notes: Optional[str]


class AgentState(TypedDict):
    """Master state passed through the LangGraph pipeline."""

    # ── Input ─────────────────────────────────────────────────
    input: ConferenceInput

    # ── Agent outputs ─────────────────────────────────────────
    sponsors:     Optional[list[dict]]   # Sponsor Agent output
    speakers:     Optional[list[dict]]   # Speaker Agent output
    exhibitors:   Optional[list[dict]]   # Exhibitor Agent output
    venues:       Optional[list[dict]]   # Venue Agent output
    pricing:      Optional[dict]         # Pricing & Footfall Agent output
    communities:  Optional[list[dict]]   # Community & GTM Agent output
    ops_plan:     Optional[dict]         # Event Ops Agent output

    # ── Final output ──────────────────────────────────────────
    final_plan:   Optional[str]          # Master orchestrator summary

    # ── Internal ──────────────────────────────────────────────
    errors:       Optional[list[str]]    # Any agent errors
    messages:     list[Any]              # LangGraph message history
