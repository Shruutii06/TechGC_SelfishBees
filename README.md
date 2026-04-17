# 🏟️ AI Conference Organizer — Multi-Agent System

> **TechGC · Team Code - 11052**
> An autonomous, LangGraph-powered multi-agent system for end-to-end conference and sports event planning — from sponsor discovery to ops scheduling.

---
## Deployed Platform

You can access the live application here:

https://techgcselfishbees-iy6nfbxer5j5zeirjkbynj.streamlit.app/

---
##  Overview

The **AI Conference Organizer** is a production-ready multi-agent pipeline that automates the entire lifecycle of planning a large-scale sports or conference event. Given just a sport category, geography, and target audience size, the system orchestrates 7 specialized AI agents that work sequentially through a LangGraph state machine, each querying a ChromaDB vector database (RAG) backed by 8 curated CSV datasets, and ultimately synthesizing a full markdown event plan.

**Built for:** Sports events, fan fests, conferences, tournaments across supported geographies and sports.

---

##  Architecture

```
CLI Input (main.py)
    │
    ▼
Input Validator (validator.py)
    │  Normalises sport + geography → raises ValidationError if unsupported
    ▼
LangGraph Pipeline (orchestrator.py)
    │
    ├──► [1] SponsorAgent        →  sponsors_master.csv
    ├──► [2] SpeakerAgent        →  speakers_master.csv
    ├──► [3] ExhibitorAgent      →  exhibitors_master.csv
    ├──► [4] VenueAgent          →  venues_master.csv
    ├──► [5] PricingAgent        →  ticket_pricing_master.csv + attendance_reference.csv
    ├──► [6] CommunityAgent      →  communities_master.csv
    ├──► [7] OpsAgent            →  (uses Speaker + Venue outputs)
    │
    ▼
Synthesiser (LLM)
    │
    ▼
Final Markdown Report  →  output/plan.md
Raw Agent Debug JSON   →  output/plan_debug.json
```

All 6 specialist agents run **sequentially** (to prevent rate-limit spikes), feeding into the Ops Agent and then a final synthesis step.

---

##  Project Structure

```
conference_agent/
│
├── agents/
│   ├── __init__.py
│   ├── state.py                 ← Shared AgentState TypedDict schema
│   ├── sponsor_agent.py         ← Sponsor discovery & deal estimation
│   ├── speaker_agent.py         ← Speaker/athlete recommendations
│   ├── exhibitor_agent.py       ← Exhibitor company suggestions
│   ├── venue_agent.py           ← Venue selection with capacity matching
│   ├── pricing_agent.py         ← Ticket pricing tiers + revenue model
│   ├── community_agent.py       ← GTM strategy + community targeting
│   └── ops_agent.py             ← Full-day agenda + resource plan
│
├── rag/
│   ├── __init__.py
│   ├── ingest.py                ← Run ONCE to embed CSVs into ChromaDB
│   ├── retriever.py             ← Shared RAG query utility (singleton client)
│   └── csv_fallback.py         ← Direct CSV fallback when RAG returns < 3 results
│
├── data/                        ← Place all 8 master CSVs here
│   ├── events_master.csv
│   ├── sponsors_master.csv
│   ├── speakers_master.csv
│   ├── venues_master.csv
│   ├── ticket_pricing_master.csv
│   ├── communities_master.csv
│   ├── exhibitors_master.csv
│   ├── attendance_reference.csv
│   └── olympics_reference.csv
│
├── chroma_db/                   ← Auto-generated ChromaDB vector store (after ingest)
│
├── output/                      ← Auto-generated output directory
│   ├── plan.md                  ← Full event plan (markdown)
│   └── plan_debug.json          ← Raw agent outputs (JSON)
│
├── orchestrator.py              ← LangGraph master pipeline builder
├── main.py                      ← CLI entry point
├── validator.py                 ← Input normalisation & validation
├── config.py                    ← Supported sports, geographies, audience ranges
├── app.py                       ← (Reserved for future web interface)
├── requirements.txt
├── .env.example
└── README.md
```

---

##  Datasets

| File | Rows | Used By |
|---|---|---|
| `events_master.csv` | 1,351 | All agents (context) |
| `sponsors_master.csv` | 102 | Sponsor Agent |
| `speakers_master.csv` | 736 | Speaker Agent |
| `venues_master.csv` | 692 | Venue Agent |
| `ticket_pricing_master.csv` | 20 | Pricing Agent |
| `communities_master.csv` | 33 | Community Agent |
| `exhibitors_master.csv` | 36 | Exhibitor Agent |
| `attendance_reference.csv` | — | Pricing Agent (footfall model) |
| `olympics_reference.csv` | 42 | Pricing Agent (reference) |

---

##  Tech Stack

| Component | Technology |
|---|---|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM inference | [Groq API](https://groq.com) — `llama-3.3-70b-versatile` + `llama-3.1-8b-instant` |
| Vector database | [ChromaDB](https://www.trychroma.com) (local, persistent) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, no API key needed) |
| LLM framework | [LangChain](https://python.langchain.com) |
| Data processing | Pandas |
| Language | Python 3.10+ |

---

##  Setup

### Prerequisites
- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier available)

### Step 1 — Clone & Install Dependencies

```bash
git clone https://github.com/Shruutii06/TechGC_SelfishBees.git
cd TechGC_SelfishBees
pip install -r requirements.txt
```

### Step 2 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

### Step 3 — Add Data Files

Place all 8 master CSV files into the `data/` directory:

```bash
mkdir -p data
# Copy your CSVs into data/
```

### Step 4 — Ingest CSVs into ChromaDB *(Run Once)*

```bash
python rag/ingest.py --data_dir ./data
```

This embeds all datasets into a local ChromaDB vector store at `./chroma_db/`. Takes ~2–3 minutes on first run. Re-run only if your CSVs change.

---

##  Running the System

### Basic Usage

```bash
python main.py \
    --category "cricket" \
    --geography "India" \
    --audience 50000 \
    --name "IPL Fan Fest 2026"
```

### With Budget

```bash
python main.py \
    --category "soccer" \
    --geography "Europe" \
    --audience 20000 \
    --budget 2000000 \
    --name "UEFA Fan Conference 2026"
```

### More Examples

```bash
# Basketball event in the USA
python main.py --category "basketball" --geography "USA" --audience 15000

# Formula 1 conference in the UK
python main.py --category "formula1" --geography "UK" --audience 8000 --budget 1000000

# Kabaddi event in India
python main.py --category "kabaddi" --geography "India" --audience 5000 --name "PKL Summit 2026"

# List all supported inputs
python main.py --list-supported
```

### All CLI Arguments

| Argument | Required | Description |
|---|---|---|
| `--category` | ✅ | Sport or event category (e.g. `cricket`, `soccer`, `f1`) |
| `--geography` | ✅ | Target geography (e.g. `India`, `USA`, `Europe`) |
| `--audience` | ✅ | Target audience size (500 – 100,000) |
| `--budget` | ❌ | Total budget in USD |
| `--name` | ❌ | Custom event name |
| `--notes` | ❌ | Additional notes passed to agents |
| `--output` | ❌ | Output file path (default: `output/plan.md`) |
| `--list-supported` | ❌ | Print all valid inputs and exit |

---

##  Supported Inputs

### Sports / Categories

| Sport | Aliases Accepted |
|---|---|
| `soccer` | soccer |
| `football` | football, american football, nfl |
| `cricket` | cricket, ipl, t20, odi |
| `basketball` | basketball, nba |
| `tennis` | tennis |
| `formula1` | formula1, formula 1, f1 |
| `kabaddi` | kabaddi, pkl, pro kabaddi |
| `hockey` | hockey, ice hockey, nhl |
| `baseball` | baseball, mlb |
| `mma` | mma, ufc |
| `golf` | golf |
| `boxing` | boxing |
| `rugby` | rugby |

### Geographies

`USA`, `England`, `France`, `Spain`, `Germany`, `Italy`, `India`, `UK`, `Europe`, `Global`

*(Case-insensitive; aliases like "United States", "America", "United Kingdom" are auto-normalised.)*

### Audience Size

`500` to `100,000`

---

##  Output Format

The system produces two files in the `output/` directory:

### `plan.md` — Full Event Plan

A structured markdown report containing:
1. Executive Summary
2. Sponsor Recommendations (with deal ranges)
3. Speaker Lineup
4. Exhibitor List
5. Venue Shortlist
6. Ticket Pricing Model + Revenue Projection
7. GTM Strategy & Community Targeting
8. Full Day Agenda
9. Resource & Ops Plan
10. Risk Notes

### `plan_debug.json` — Raw Agent Outputs

Full JSON dump of every agent's raw structured output — useful for debugging, integration, or downstream processing.

---

##  Agent Details

### 1. Sponsor Agent
Queries the sponsors database for brands that have sponsored similar leagues/events. Returns up to 8 sponsors with type, relevance reasoning, and estimated deal ranges.

**Model:** `llama-3.3-70b-versatile` · **Max tokens:** 1000

### 2. Speaker Agent
Finds relevant athletes, analysts, or domain experts from the speakers dataset. Returns up to 5 speakers with nationality, influence level, and recommendation rationale.

**Model:** `llama-3.1-8b-instant` · **Max tokens:** 900

### 3. Exhibitor Agent
Recommends companies that exhibit at sports events, filtered by category and geography. Returns booth tier recommendations (Platinum / Gold / Silver).

**Model:** `llama-3.3-70b-versatile` · **Max tokens:** 400

### 4. Venue Agent
Matches venues by sport suitability, capacity, and geography. Returns top 5 venues ranked by fit, with estimated rental cost ranges.

**Model:** `llama-3.3-70b-versatile` · **Max tokens:** 1000

### 5. Pricing Agent
Builds a multi-tier ticket pricing model using historical benchmark data. Outputs pricing tiers, total revenue projection, break-even attendance, and confidence score.

**Model:** `llama-3.3-70b-versatile` · **Max tokens:** 400

### 6. Community Agent
Identifies target fan communities (Reddit, Discord, Web Forums, Apps) and produces a 12-week GTM strategy with channel mix and key messages.

**Model:** `llama-3.3-70b-versatile` · **Max tokens:** 800

### 7. Ops Agent
Takes the Speaker and Venue outputs and constructs a complete 1-day event schedule (9 AM – 6 PM) with sessions, breaks, resource requirements, and equipment checklist.

**Model:** `llama-3.1-8b-instant` · **Max tokens:** 1000

---

##  Requirements

```
langgraph
langchain
langchain-groq
langchain-core
chromadb
sentence-transformers
pandas
tqdm
python-dotenv
```

Install all with:
```bash
pip install -r requirements.txt
```

---


---

*Questions or issues? Open a GitHub issue at [TechGC_SelfishBees](https://github.com/Shruutii06/TechGC_SelfishBees/issues).*
