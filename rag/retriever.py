"""
RAG Retriever
Shared utility used by all agents to query ChromaDB collections.
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import Optional

CHROMA_PATH = "./chroma_db"

# Singleton client — initialised once, reused across all agents
_client: Optional[chromadb.Client] = None
_ef = None


def _get_client():
    global _client, _ef
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _client, _ef


def query(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
    where: Optional[dict] = None,
) -> list[dict]:
    """
    Query a ChromaDB collection.

    Args:
        collection_name: One of: events, sponsors, speakers, venues,
                         ticket_pricing, communities, exhibitors, olympics
        query_text:      Natural language query string
        n_results:       Number of results to return
        where:           Optional metadata filter e.g. {"sport": "Football"}

    Returns:
        List of dicts, each with keys: text, metadata, distance
    """
    client, ef = _get_client()

    try:
        coll = client.get_collection(name=collection_name, embedding_function=ef)
    except Exception:
        return []

    kwargs = {"query_texts": [query_text], "n_results": n_results}
    if where:
        kwargs["where"] = where

    results = coll.query(**kwargs)

    output = []
    docs      = results.get("documents", [[]])[0]
    metas     = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        output.append({"text": doc, "metadata": meta, "distance": round(dist, 4)})

    return output


def format_results(results: list[dict], max_items: int = 5) -> str:
    """Format retrieval results as a clean string for LLM context."""
    if not results:
        return "No relevant data found."
    lines = []
    for i, r in enumerate(results[:max_items], 1):
        lines.append(f"{i}. {r['text']}")
        if r["metadata"]:
            meta_str = " | ".join(
                f"{k}: {v}" for k, v in r["metadata"].items() if v
            )
            if meta_str:
                lines.append(f"   → {meta_str}")
    return "\n".join(lines)
