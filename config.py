"""
Data Coverage Config
Defines exactly what the system can confidently handle
based on actual dataset coverage.
"""

# ── Supported sports (well covered across events + speakers + venues) ──
SUPPORTED_SPORTS = [
    "soccer",
    "football",       # NFL / American football
    "tennis",
    "cricket",
    "formula1",
    "basketball",
    "hockey",
    "baseball",
    "mma",
    "golf",
    "boxing",
    "rugby",
]

# ── Supported geographies (well covered in events + pricing + communities) ──
SUPPORTED_GEOGRAPHIES = [
    "USA",
    "England",
    "France",
    "Spain",
    "Germany",
    "Italy",
    "India",
    "Global",
    "Europe",       # maps to England/France/Spain/Germany/Italy
    "UK",
]

# ── Supported leagues (sponsors data covers these well) ──
SUPPORTED_LEAGUES = [
    "NFL",
    "NBA",
    "IPL",
    "Premier League",
    "Formula 1",
    "MLB",
    "Champions League",
    "UFC",
    "NHL",
    "La Liga",
    "Bundesliga",
]

# ── Audience size limits (based on venue capacity data) ──
MIN_AUDIENCE = 500
MAX_AUDIENCE = 100_000

# ── Geography normalisation map ──
# Maps user inputs → internal keys used in data
GEOGRAPHY_NORM = {
    "europe":           "Europe",
    "uk":               "UK",
    "united kingdom":   "UK",
    "england":          "England",
    "france":           "France",
    "spain":            "Spain",
    "germany":          "Germany",
    "italy":            "Italy",
    "usa":              "USA",
    "united states":    "USA",
    "us":               "USA",
    "america":          "USA",
    "india":            "India",
    "global":           "Global",
}

# ── Sport normalisation map ──
SPORT_NORM = {
    "football":           "football",
    "american football":  "football",
    "nfl":                "football",
    "soccer":             "soccer",
    "football (soccer)":  "soccer",
    "tennis":             "tennis",
    "cricket":            "cricket",
    "ipl":                "cricket",
    "formula 1":          "formula1",
    "formula1":           "formula1",
    "f1":                 "formula1",
    "basketball":         "basketball",
    "nba":                "basketball",
    "hockey":             "hockey",
    "ice hockey":         "hockey",
    "nhl":                "hockey",
    "baseball":           "baseball",
    "mlb":                "baseball",
    "mma":                "mma",
    "ufc":                "mma",
    "golf":               "golf",
    "boxing":             "boxing",
    "rugby":              "rugby",
}
