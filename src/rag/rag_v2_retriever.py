"""Retrieval engine for the RAG V2 ChromaDB knowledge base.

Connects to vector_db/ndi_rag_v2_chroma (built by rag_v2_builder.py) and
exposes a search() function. This module is independent of RAG V1
(retrieval_engine.py) and does not touch the V1 vector store.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import arabic_reshaper
from bidi.algorithm import get_display
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

VECTOR_DB_DIR_NAME = "vector_db/ndi_rag_v2_chroma"
COLLECTION_NAME = "ndi_rag_v2"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_TOP_K = 10
PREVIEW_LENGTH = 1500

TEST_QUESTIONS = [
    "ما هي متطلبات الدليل DC.M.6؟",
]


def _display_arabic(text: str) -> str:
    """Reshapes and reorders Arabic text for correct terminal display only.

    Args:
        text: Raw text that may contain Arabic script.

    Returns:
        A display-ready string. The reshaping/bidi transform is applied only
        for presentation and must never be used for storage or search.
    """
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


class RagV2Retriever:
    """Searches the persisted RAG V2 ChromaDB knowledge base using semantic similarity."""

    def __init__(
        self,
        vector_db_dir: Path | str,
        collection_name: str = COLLECTION_NAME,
        embedding_model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        """Connects to the ChromaDB collection and loads the embedding model.

        Args:
            vector_db_dir: Path to the persistent ChromaDB directory.
            collection_name: Name of the collection to search.
            embedding_model_name: Sentence embedding model used to embed queries.
        """
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
        self._store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(vector_db_dir),
        )

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
        """Runs a similarity search with relevance scores against the knowledge base.

        Args:
            query: Query text.
            top_k: Number of results to return.

        Returns:
            A list of dictionaries, each with content, score, and source_file,
            ordered from most to least relevant.
        """
        results = self._store.similarity_search_with_relevance_scores(query, k=top_k)

        return [
            {
                "content": document.page_content,
                "score": score,
                "source_file": document.metadata.get("source_file"),
                "page": document.metadata.get("page"),
            }
            for document, score in results
        ]


def main() -> None:
    """Runs the sample test questions against the RAG V2 knowledge base and prints results."""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    project_root = Path(__file__).resolve().parents[2]
    vector_db_dir = project_root / VECTOR_DB_DIR_NAME

    retriever = RagV2Retriever(vector_db_dir)

    for question in TEST_QUESTIONS:
        print("=" * 50)
        print("Question:")
        print(_display_arabic(question))
        print("\nTop Results")

        for rank, result in enumerate(retriever.search(question, top_k=DEFAULT_TOP_K), start=1):
            preview = result["content"][:PREVIEW_LENGTH]
            print(f"\nRank {rank}")
            print(f"Score: {result['score']:.4f}")
            print(f"Source: {result['source_file']} (page {result['page']})")
            print(f"Preview: {_display_arabic(preview)}")
        print()


if __name__ == "__main__":
    main()
