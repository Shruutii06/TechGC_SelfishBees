# 🏟️ AI Conference Organizer — Multi-Agent System

A LangGraph + ChromaDB powered multi-agent system for autonomous conference planning.

---

## 📁 Project Structure

```
conference_agent/
├── data/                        ← Put all 8 master CSVs here
│   ├── events_master.csv
│   ├── sponsors_master.csv
│   ├── speakers_master.csv
│   ├── venues_master.csv
│   ├── ticket_pricing_master.csv
│   ├── communities_master.csv
│   ├── exhibitors_master.csv
│   └── olympics_reference.csv
│
├── rag/
│   ├── ingest.py                ← Run ONCE to embed CSVs into ChromaDB
│   └── retriever.py             ← Shared RAG query utility
│
├── agents/
│   ├── state.py                 ← Shared AgentState schema
│   ├── sponsor_agent.py         ← Sponsor recommendations
│   ├── speaker_agent.py         ← Speaker/artist discovery
│   ├── exhibitor_agent.py       ← Exhibitor suggestions
│   ├── venue_agent.py           ← Venue recommendations
│   ├── pricing_agent.py         ← Ticket pricing + footfall model
│   ├── community_agent.py       ← GTM + community strategy
│   └── ops_agent.py             ← Agenda + resource planning
│
├── orchestrator.py              ← LangGraph master pipeline
├── main.py                      ← CLI entry point
├── requirements.txt
└── .env.example
```

---

## ⚡ Setup (3 steps)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Set your Groq API key
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Step 3 — Ingest your CSVs into ChromaDB (run ONCE)
```bash
# Copy your 8 master CSVs into the data/ folder first
mkdir data
cp /path/to/your/csvs/*.csv data/

python rag/ingest.py --data_dir ./data
```

This will embed all 8 datasets into a local ChromaDB at `./chroma_db/`.
Takes ~2-3 minutes on first run.

---

## 🚀 Run the Agent System

```bash
python main.py \
    --category "Sports" \
    --geography "India" \
    --audience 5000 \
    --budget 500000 \
    --name "TechSport India 2026"
```

### More examples:
```bash
# AI Conference in Singapore
python main.py --category "AI Conference" --geography "Singapore" --audience 2000 --name "AI Summit Asia 2026"

# Music Festival in Europe
python main.py --category "Music Festival" --geography "Europe" --audience 20000 --budget 2000000

# Sports event in USA
python main.py --category "Basketball Tournament" --geography "USA" --audience 15000
```

Output is saved to `output/plan.md` (the full markdown report) and `output/plan_debug.json` (raw agent outputs).

---

## 🤖 Agent Architecture

```
START
  │
  ├──► SponsorAgent      → sponsors_master.csv
  ├──► SpeakerAgent      → speakers_master.csv
  ├──► ExhibitorAgent    → exhibitors_master.csv
  ├──► VenueAgent        → venues_master.csv
  ├──► PricingAgent      → ticket_pricing_master.csv + olympics_reference.csv
  └──► CommunityAgent    → communities_master.csv
         │
         ▼
       OpsAgent          (uses Speaker + Venue outputs)
         │
         ▼
      Synthesiser        → Final Markdown Report
         │
        END
```

All 6 specialist agents run in **parallel**, then the Ops Agent and Synthesiser finalise the plan.

---

## 📊 Datasets Used

| File | Rows | Agent |
|---|---|---|
| events_master.csv | 1,351 | All agents (context) |
| sponsors_master.csv | 102 | Sponsor Agent |
| speakers_master.csv | 736 | Speaker Agent |
| venues_master.csv | 692 | Venue Agent |
| ticket_pricing_master.csv | 20 | Pricing Agent |
| communities_master.csv | 33 | Community Agent |
| exhibitors_master.csv | 36 | Exhibitor Agent |
| olympics_reference.csv | 42 | Pricing Agent (reference) |

---

## 🔧 Customisation

- **Swap LLM**: Change `ChatAnthropic(model="claude-sonnet-4-20250514")` to any LangChain-compatible model
- **Add agents**: Create a new file in `agents/`, add it to `orchestrator.py`
- **Add data**: Drop new CSVs in `data/`, add config to `rag/ingest.py`, re-run ingest
