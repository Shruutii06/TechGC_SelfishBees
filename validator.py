"""
Input Validator
Checks user inputs against actual data coverage before running agents.
Normalises sport and geography to match dataset keys.
"""

from config import (
    SUPPORTED_SPORTS, SUPPORTED_GEOGRAPHIES, SUPPORTED_LEAGUES,
    MIN_AUDIENCE, MAX_AUDIENCE, GEOGRAPHY_NORM, SPORT_NORM
)


class ValidationError(Exception):
    pass


def normalise_sport(raw: str) -> str:
    """Normalise sport string to dataset key. Returns None if not supported."""
    key = raw.strip().lower()
    return SPORT_NORM.get(key)


def normalise_geography(raw: str) -> str:
    """Normalise geography string to dataset key. Returns None if not supported."""
    key = raw.strip().lower()
    return GEOGRAPHY_NORM.get(key)


def validate_and_normalise(
    event_category: str,
    geography: str,
    target_audience_size: int,
    budget_usd: float | None = None,
) -> dict:
    """
    Validate and normalise inputs.
    Returns cleaned dict or raises ValidationError with a helpful message.
    """
    errors = []
    suggestions = {}

    # ── Sport / Category ──────────────────────────────────────────────────
    sport_norm = normalise_sport(event_category)
    if sport_norm is None:
        errors.append(
            f"'{event_category}' is not well supported by the current dataset.\n"
            f"  Supported sports: {', '.join(SUPPORTED_SPORTS)}\n"
            f"  Tip: Try one of the above, e.g. --category 'soccer' or --category 'cricket'"
        )
    else:
        suggestions["event_category"] = sport_norm

    # ── Geography ─────────────────────────────────────────────────────────
    geo_norm = normalise_geography(geography)
    if geo_norm is None:
        errors.append(
            f"'{geography}' is not well covered in the current dataset.\n"
            f"  Supported geographies: {', '.join(SUPPORTED_GEOGRAPHIES)}\n"
            f"  Tip: Try one of the above, e.g. --geography 'India' or --geography 'Europe'"
        )
    else:
        suggestions["geography"] = geo_norm

    # ── Audience size ──────────────────────────────────────────────────────
    if not (MIN_AUDIENCE <= target_audience_size <= MAX_AUDIENCE):
        errors.append(
            f"Audience size {target_audience_size:,} is outside supported range "
            f"({MIN_AUDIENCE:,} – {MAX_AUDIENCE:,})."
        )

    # ── Raise if any errors ───────────────────────────────────────────────
    if errors:
        msg = "\n\n❌ Input validation failed:\n\n" + "\n\n".join(errors)
        raise ValidationError(msg)

    return {
        "event_category": suggestions.get("event_category", event_category),
        "geography":      suggestions.get("geography", geography),
        "target_audience_size": target_audience_size,
        "budget_usd":     budget_usd,
    }


def print_supported_options():
    """Print all supported options to the console."""
    print("\n📋 Supported inputs for this system:")
    print(f"\n  Sports/Categories: {', '.join(SUPPORTED_SPORTS)}")
    print(f"\n  Geographies:       {', '.join(SUPPORTED_GEOGRAPHIES)}")
    print(f"\n  Audience size:     {MIN_AUDIENCE:,} – {MAX_AUDIENCE:,}")
    print(f"\n  Known leagues:     {', '.join(SUPPORTED_LEAGUES)}")
