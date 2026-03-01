"""
RAG Engine for Sasha AI v2

Uses ChromaDB as a vector store and Ollama's nomic-embed-text model to embed
knowledge entries. At query time the top-K most relevant chunks are retrieved
and injected into the LLM context window alongside the base system prompt.

Architecture:
  Knowledge DB (SQLite)  →  embed via Ollama  →  ChromaDB collection
  User query  →  embed  →  similarity search  →  top-K chunks
  top-K chunks + base prompt  →  Ollama LLM  →  response
"""

import logging
import httpx
import chromadb
from chromadb.config import Settings
from typing import Optional
from config.app_config import config

logger = logging.getLogger("sasha.rag")

COLLECTION_NAME = "sasha_knowledge"


class RAGEngine:
    """
    Manages the ChromaDB vector store and provides retrieval-augmented
    generation helpers.
    """

    def __init__(self):
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    # ── Lazy init ────────────────────────────────────────────────────────────

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        self._client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    # ── Embedding via Ollama ─────────────────────────────────────────────────

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Call Ollama /api/embed and return a list of embedding vectors."""
        if not texts:
            return []
        try:
            with httpx.Client(timeout=30) as client:
                r = client.post(
                    f"{config.OLLAMA_URL}/api/embed",
                    json={"model": config.OLLAMA_EMBED_MODEL, "input": texts},
                )
                r.raise_for_status()
                return r.json()["embeddings"]
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    # ── Index management ─────────────────────────────────────────────────────

    def upsert_entry(self, entry_id: int, category: str, content: str) -> None:
        """Add or update a single knowledge entry in the vector store."""
        doc_id = str(entry_id)
        text = f"{category}: {content}"
        try:
            embeddings = self._embed([text])
            col = self._get_collection()
            col.upsert(
                ids=[doc_id],
                embeddings=embeddings,
                documents=[text],
                metadatas=[{"category": category, "knowledge_id": entry_id}],
            )
            logger.info(f"Upserted RAG entry id={entry_id} category={category}")
        except Exception as e:
            logger.error(f"Failed to upsert RAG entry {entry_id}: {e}")
            raise

    def delete_entry(self, entry_id: int) -> None:
        """Remove a knowledge entry from the vector store."""
        try:
            col = self._get_collection()
            col.delete(ids=[str(entry_id)])
            logger.info(f"Deleted RAG entry id={entry_id}")
        except Exception as e:
            logger.error(f"Failed to delete RAG entry {entry_id}: {e}")

    def rebuild_index(self, entries: list[dict]) -> int:
        """
        Full rebuild of the vector store from a list of knowledge dicts.
        Each dict must have keys: id, category, content.
        Returns number of entries indexed.
        """
        if not entries:
            logger.info("No active entries to index.")
            return 0

        col = self._get_collection()

        # Wipe and re-index
        try:
            self._client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        col = self._collection

        ids = [str(e["id"]) for e in entries]
        texts = [f"{e['category']}: {e['content']}" for e in entries]
        metadatas = [{"category": e["category"], "knowledge_id": e["id"]} for e in entries]

        # Batch embed (Ollama accepts arrays)
        BATCH = 32
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            all_embeddings.extend(self._embed(batch))

        col.upsert(
            ids=ids,
            embeddings=all_embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info(f"Rebuilt RAG index with {len(entries)} entries.")
        return len(entries)

    def get_index_count(self) -> int:
        """Return number of entries currently in the vector store."""
        try:
            return self._get_collection().count()
        except Exception:
            return 0

    # ── Retrieval ────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """
        Retrieve the most relevant knowledge chunks for a query.
        Returns a list of dicts with keys: content, category, score, knowledge_id.
        """
        k = top_k if top_k is not None else config.RAG_TOP_K
        try:
            embeddings = self._embed([query])
            col = self._get_collection()
            count = col.count()
            if count == 0:
                return []

            actual_k = min(k, count)
            results = col.query(
                query_embeddings=embeddings,
                n_results=actual_k,
                include=["documents", "metadatas", "distances"],
            )

            chunks = []
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for doc, meta, dist in zip(docs, metas, distances):
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to a 0-1 similarity score
                similarity = 1.0 - (dist / 2.0)
                chunks.append(
                    {
                        "content": doc,
                        "category": meta.get("category", ""),
                        "knowledge_id": meta.get("knowledge_id", -1),
                        "score": round(similarity, 4),
                    }
                )
            return chunks
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return []

    # ── Context builder ──────────────────────────────────────────────────────

    def build_rag_context(self, query: str) -> str:
        """
        Return a formatted string of the most relevant knowledge chunks
        to be injected into the LLM system prompt.
        """
        chunks = self.retrieve(query)
        if not chunks:
            return ""

        lines = ["Relevant facts retrieved for this question:"]
        for chunk in chunks:
            lines.append(f"- {chunk['content']}")
        return "\n".join(lines)


# Global singleton
rag_engine = RAGEngine()
