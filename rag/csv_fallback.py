"""
CSV Fallback Utility
When ChromaDB RAG returns fewer than MIN_RESULTS,
directly load rows from the CSV and format them as context.
This ensures agents always have real data even before re-ingestion.
"""

import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MIN_RESULTS = 3


def _load(filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def speakers_fallback(sport: str, geography: str, n: int = 10) -> str:
    df = _load("speakers_master.csv")
    if df.empty:
        return ""
    sport_lower = sport.lower()
    mask = df["sport"].astype(str).str.lower().str.contains(sport_lower, na=False)
    filtered = df[mask]
    if len(filtered) < 3:
        filtered = df  # broaden if too few
    filtered = filtered.head(n)
    lines = []
    for _, r in filtered.iterrows():
        lines.append(
            f"name: {r.get('name','')} | sport: {r.get('sport','')} | "
            f"role: {r.get('organization','')} | expertise: {r.get('expertise','')} | "
            f"nationality: {r.get('nationality','')}"
        )
    return "\n".join(lines)


def venues_fallback(sport: str, geography: str, n: int = 8) -> str:
    df = _load("venues_master.csv")
    if df.empty:
        return ""
    sport_lower = sport.lower()
    geo_lower   = geography.lower()
    mask_sport = df["sport"].astype(str).str.lower().str.contains(sport_lower, na=False)
    mask_geo   = (
        df["city"].astype(str).str.lower().str.contains(geo_lower, na=False) |
        df["country"].astype(str).str.lower().str.contains(geo_lower, na=False)
    )
    filtered = df[mask_sport & mask_geo]
    if len(filtered) < 3:
        filtered = df[mask_sport]
    if len(filtered) < 3:
        filtered = df
    filtered = filtered[filtered["capacity"].notna()].sort_values("capacity", ascending=False).head(n)
    lines = []
    for _, r in filtered.iterrows():
        lines.append(
            f"venue_name: {r.get('venue_name','')} | city: {r.get('city','')} | "
            f"country: {r.get('country','')} | capacity: {r.get('capacity','')} | "
            f"sport: {r.get('sport','')}"
        )
    return "\n".join(lines)


def sponsors_fallback(sport: str, geography: str, n: int = 10) -> str:
    df = _load("sponsors_master.csv")
    if df.empty:
        return ""
    sport_lower = sport.lower()
    mask = (
        df["event_league"].astype(str).str.lower().str.contains(sport_lower, na=False) |
        df["sponsor_type"].astype(str).str.lower().str.contains("india", na=False) |
        df["event_league"].astype(str).str.lower().isin(["ipl","pkl","odi world cup","t20 world cup"])
    )
    filtered = df[mask]
    if len(filtered) < 3:
        filtered = df
    filtered = filtered.head(n)
    lines = []
    for _, r in filtered.iterrows():
        lines.append(
            f"sponsor_name: {r.get('sponsor_name','')} | type: {r.get('sponsor_type','')} | "
            f"league: {r.get('event_league','')} | geography: {r.get('geography','')}"
        )
    return "\n".join(lines)


def exhibitors_fallback(sport: str, geography: str, n: int = 10) -> str:
    df = _load("exhibitors_master.csv")
    if df.empty:
        return ""
    sport_lower = sport.lower()
    mask = df["sport"].astype(str).str.lower().str.contains(sport_lower, na=False) if "sport" in df.columns else pd.Series([True]*len(df))
    filtered = df[mask]
    if len(filtered) < 3:
        filtered = df
    filtered = filtered.head(n)
    lines = []
    for _, r in filtered.iterrows():
        lines.append(
            f"company_name: {r.get('company_name','')} | category: {r.get('category','')} | "
            f"type: {r.get('company_type','')} | activation: {r.get('sub_category','')} | "
            f"geography: {r.get('geography','')}"
        )
    return "\n".join(lines)


def pricing_fallback(sport: str, geography: str, n: int = 10) -> str:
    df = _load("ticket_pricing_master.csv")
    if df.empty:
        return ""
    sport_lower = sport.lower()
    mask = df["sport"].astype(str).str.lower().str.contains(sport_lower, na=False)
    filtered = df[mask]
    if len(filtered) < 2:
        filtered = df
    filtered = filtered.head(n)
    lines = []
    for _, r in filtered.iterrows():
        lines.append(
            f"event: {r.get('event_name','')} | tier: {r.get('ticket_tier','')} | "
            f"price_usd: {r.get('avg_price_usd','')} | price_inr: {r.get('price_inr','')} | "
            f"attendance: {r.get('typical_attendance','')} | sport: {r.get('sport','')}"
        )
    return "\n".join(lines)


def attendance_fallback(sport: str) -> str:
    df = _load("attendance_reference.csv")
    if df.empty:
        return ""
    sport_lower = sport.lower()
    mask = df["sport"].astype(str).str.lower().str.contains(sport_lower, na=False)
    filtered = df[mask]
    if filtered.empty:
        filtered = df
    lines = []
    for _, r in filtered.iterrows():
        lines.append(
            f"event: {r.get('event','')} | avg_attendance: {r.get('avg_attendance','')} | "
            f"total_attendance: {r.get('total_attendance','')} | year: {r.get('year','')}"
        )
    return "\n".join(lines)


def get_context(collection: str, rag_results: list, sport: str, geography: str) -> str:
    """
    Returns RAG results if sufficient, else falls back to CSV.
    collection: 'speakers' | 'venues' | 'sponsors' | 'exhibitors' | 'ticket_pricing'
    """
    if len(rag_results) >= MIN_RESULTS:
        from rag.retriever import format_results
        return format_results(rag_results)

    # Fallback to CSV
    fallbacks = {
        "speakers":      lambda: speakers_fallback(sport, geography),
        "venues":        lambda: venues_fallback(sport, geography),
        "sponsors":      lambda: sponsors_fallback(sport, geography),
        "exhibitors":    lambda: exhibitors_fallback(sport, geography),
        "ticket_pricing":lambda: pricing_fallback(sport, geography),
    }
    fn = fallbacks.get(collection)
    result = fn() if fn else ""
    if result:
        return f"[CSV Fallback — direct data]\n{result}"
    return "No relevant data found."
