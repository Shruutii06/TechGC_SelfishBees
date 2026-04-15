"""
RAG Ingestion Pipeline
Embeds all 8 CSV datasets into ChromaDB collections.
Run this ONCE before starting the agent system.

Usage:
    python rag/ingest.py --data_dir ./data
"""

import os
import argparse
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

# ── Config ──────────────────────────────────────────────────────────────────
CHROMA_PATH = "./chroma_db"

# Map: CSV filename → ChromaDB collection name + which columns to embed
DATASET_CONFIG = {
    "events_master.csv": {
        "collection": "events",
        "text_cols": ["name", "sport", "league", "venue", "city", "country"],
        "meta_cols": ["date", "home_team", "away_team", "status", "source"],
        "description": "Sports/conference events 2025-2026",
    },
    "sponsors_master.csv": {
        "collection": "sponsors",
        "text_cols": ["event_league", "sponsor_name", "sponsor_type"],
        "meta_cols": ["league_code", "deal_amount", "source"],
        "description": "Known sponsors by league/event",
    },
    "speakers_master.csv": {
        "collection": "speakers",
        "text_cols": ["name", "sport", "organization", "nationality"],
        "meta_cols": ["extra_info", "source"],
        "description": "Athletes and speakers/subject matter experts",
    },
    "venues_master.csv": {
        "collection": "venues",
        "text_cols": ["venue_name", "sport", "city", "country"],
        "meta_cols": ["capacity", "source"],
        "description": "Venues with capacity info",
    },
    "ticket_pricing_master.csv": {
        "collection": "ticket_pricing",
        "text_cols": ["event_name", "sport", "geography", "ticket_tier"],
        "meta_cols": ["typical_attendance", "avg_price_usd", "vip_price_usd",
                      "annual_revenue_est_usd", "source"],
        "description": "Ticket pricing and footfall benchmarks",
    },
    "communities_master.csv": {
        "collection": "communities",
        "text_cols": ["community_name", "platform", "sport", "geography", "niche"],
        "meta_cols": ["members", "description", "url", "organization", "source"],
        "description": "Sports/topic communities for GTM",
    },
    "exhibitors_master.csv": {
        "collection": "exhibitors",
        "text_cols": ["company_name", "category", "sub_category", "geography", "company_type"],
        "meta_cols": ["country", "event_presence"],
        "description": "Companies that exhibit at sports events",
    },
    "olympics_reference.csv": {
        "collection": "olympics",
        "text_cols": ["edition", "season", "host_city", "country"],
        "meta_cols": ["year", "start_date", "end_date", "nations",
                      "athletes", "sports", "events", "url"],
        "description": "Historical Olympics reference data",
    },
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def row_to_text(row: pd.Series, text_cols: list[str]) -> str:
    """Concatenate key columns into a single searchable string."""
    parts = []
    for col in text_cols:
        val = str(row.get(col, "")).strip()
        if val and val.lower() not in ("nan", "none", ""):
            parts.append(f"{col}: {val}")
    return " | ".join(parts)


def row_to_meta(row: pd.Series, meta_cols: list[str]) -> dict:
    """Build metadata dict (ChromaDB requires string values)."""
    meta = {}
    for col in meta_cols:
        val = row.get(col, "")
        meta[col] = "" if pd.isna(val) else str(val)
    return meta


def ingest_csv(client: chromadb.Client, ef, csv_path: str, config: dict):
    """Load a CSV and upsert all rows into a ChromaDB collection."""
    df = pd.read_csv(csv_path)
    coll = client.get_or_create_collection(
        name=config["collection"],
        embedding_function=ef,
        metadata={"description": config["description"]},
    )

    ids, documents, metadatas = [], [], []
    for i, row in df.iterrows():
        doc = row_to_text(row, config["text_cols"])
        if not doc.strip():
            continue
        ids.append(f"{config['collection']}_{i}")
        documents.append(doc)
        metadatas.append(row_to_meta(row, config["meta_cols"]))

    # Upsert in batches of 500
    batch_size = 500
    for start in tqdm(range(0, len(ids), batch_size),
                      desc=f"  Ingesting {config['collection']}"):
        coll.upsert(
            ids=ids[start:start + batch_size],
            documents=documents[start:start + batch_size],
            metadatas=metadatas[start:start + batch_size],
        )

    print(f"  ✅ {config['collection']}: {len(ids)} rows ingested")
    return len(ids)


# ── Main ─────────────────────────────────────────────────────────────────────

def main(data_dir: str):
    print("🔧 Initialising ChromaDB at:", CHROMA_PATH)
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Use sentence-transformers for local embeddings (no API key needed)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    total = 0
    for filename, config in DATASET_CONFIG.items():
        csv_path = os.path.join(data_dir, filename)
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Skipping {filename} — file not found at {csv_path}")
            continue
        print(f"\n📄 Processing: {filename}")
        total += ingest_csv(client, ef, csv_path, config)

    print(f"\n🎉 Done! {total} total documents embedded across {len(DATASET_CONFIG)} collections.")
    print(f"   ChromaDB stored at: {CHROMA_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="./data",
                        help="Folder containing all 8 master CSVs")
    args = parser.parse_args()
    main(args.data_dir)
