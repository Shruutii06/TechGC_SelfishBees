"""
Main Entry Point
Run the Conference Organizer Agent System from the command line.

Usage:
    python main.py --category "soccer" --geography "India" --audience 5000
    python main.py --list-supported
"""

import argparse
import json
import os
from dotenv import load_dotenv
load_dotenv()

from validator import validate_and_normalise, ValidationError, print_supported_options
from orchestrator import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="AI Conference Organizer")
    parser.add_argument("--category",        default=None,  help="Sport/event category")
    parser.add_argument("--geography",       default=None,  help="Geography")
    parser.add_argument("--audience",        default=None,  type=int, help="Target audience size")
    parser.add_argument("--budget",          default=None,  type=float, help="Budget in USD (optional)")
    parser.add_argument("--name",            default=None,  help="Event name (optional)")
    parser.add_argument("--notes",           default=None,  help="Additional notes (optional)")
    parser.add_argument("--output",          default="output/plan.md", help="Output file path")
    parser.add_argument("--list-supported",  action="store_true", help="Show all supported inputs and exit")
    args = parser.parse_args()

    # Show supported options and exit
    if args.list_supported:
        print_supported_options()
        return

    # Check required args
    if not all([args.category, args.geography, args.audience]):
        parser.error("--category, --geography, and --audience are required. "
                     "Run with --list-supported to see valid options.")

    # ── Validate & normalise inputs ───────────────────────────────────────
    try:
        clean = validate_and_normalise(
            event_category        = args.category,
            geography             = args.geography,
            target_audience_size  = args.audience,
            budget_usd            = args.budget,
        )
    except ValidationError as e:
        print(str(e))
        print("\n💡 Run  python main.py --list-supported  to see all valid options.")
        return

    event_name = args.name or f"{clean['event_category'].title()} Event {clean['geography']} 2026"

    print(f"\n🚀 Starting Conference Organizer Agent System")
    print(f"   Event:    {event_name}")
    print(f"   Sport:    {clean['event_category']}")
    print(f"   Location: {clean['geography']}")
    print(f"   Audience: {clean['target_audience_size']:,}")
    if clean['budget_usd']:
        print(f"   Budget:   ${clean['budget_usd']:,.0f}")
    print("\n   Running agents... (this may take 30-60 seconds)\n")

    # ── Run pipeline ──────────────────────────────────────────────────────
    state = run_pipeline(
        event_category        = clean['event_category'],
        geography             = clean['geography'],
        target_audience_size  = clean['target_audience_size'],
        budget_usd            = clean['budget_usd'],
        event_name            = event_name,
        additional_notes      = args.notes,
    )

    # ── Print & save output ───────────────────────────────────────────────
    print("\n" + "="*60)
    print("📋 FINAL CONFERENCE PLAN")
    print("="*60)
    print(state.get("final_plan", "No plan generated."))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(state.get("final_plan", ""))
    print(f"\n✅ Plan saved to: {args.output}")

    debug_path = args.output.replace(".md", "_debug.json")
    debug_data = {k: v for k, v in state.items() if k not in ("messages", "final_plan")}
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(debug_data, f, indent=2, default=str, ensure_ascii=False)
    print(f"🔍 Raw agent outputs: {debug_path}")

    if state.get("errors"):
        print(f"\n⚠️  Agent errors: {state['errors']}")


if __name__ == "__main__":
    main()
