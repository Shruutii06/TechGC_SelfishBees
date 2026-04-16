"""
Data Coverage Config
Defines exactly what the system can confidently handle
based on actual dataset coverage.
"""

SUPPORTED_SPORTS = [
    "soccer",
    "football",
    "tennis",
    "cricket",
    "kabaddi",
    "formula1",
    "basketball",
    "hockey",
    "baseball",
    "mma",
    "golf",
    "boxing",
    "rugby",
]

SUPPORTED_GEOGRAPHIES = [
    "USA",
    "England",
    "France",
    "Spain",
    "Germany",
    "Italy",
    "India",
    "Global",
    "Europe",
    "UK",
]

SUPPORTED_LEAGUES = [
    "IPL",
    "PKL",
    "ODI World Cup",
    "T20 World Cup",
    "Kabaddi World Cup",
    "NFL",
    "NBA",
    "Premier League",
    "Formula 1",
    "MLB",
    "Champions League",
    "UFC",
    "NHL",
    "La Liga",
    "Bundesliga",
]

MIN_AUDIENCE = 500
MAX_AUDIENCE = 100_000

GEOGRAPHY_NORM = {
    "europe":         "Europe",
    "uk":             "UK",
    "united kingdom": "UK",
    "england":        "England",
    "france":         "France",
    "spain":          "Spain",
    "germany":        "Germany",
    "italy":          "Italy",
    "usa":            "USA",
    "united states":  "USA",
    "us":             "USA",
    "america":        "USA",
    "india":          "India",
    "global":         "Global",
}

SPORT_NORM = {
    "football":          "football",
    "american football": "football",
    "nfl":               "football",
    "soccer":            "soccer",
    "tennis":            "tennis",
    "cricket":           "cricket",
    "ipl":               "cricket",
    "t20":               "cricket",
    "odi":               "cricket",
    "kabaddi":           "kabaddi",
    "pkl":               "kabaddi",
    "pro kabaddi":       "kabaddi",
    "formula 1":         "formula1",
    "formula1":          "formula1",
    "f1":                "formula1",
    "basketball":        "basketball",
    "nba":               "basketball",
    "hockey":            "hockey",
    "ice hockey":        "hockey",
    "nhl":               "hockey",
    "baseball":          "baseball",
    "mlb":               "baseball",
    "mma":               "mma",
    "ufc":               "mma",
    "golf":              "golf",
    "boxing":            "boxing",
    "rugby":             "rugby",
}
