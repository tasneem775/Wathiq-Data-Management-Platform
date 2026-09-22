"""Builds the RAG V2 ChromaDB vector store from NDI framework PDF documents.

This is a fresh, independent pipeline built with LangChain loaders/splitters.
It does not read, write, or depend on any RAG V1 file (chunking.py,
chunking_manager.py, vector_store_builder.py, retrieval_engine.py) or the
V1 vector store at vector_db/ndi_sentinel_chroma.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

SOURCE_DIR_NAME = "knowledge_base/ndi_framework"
VECTOR_DB_DIR_NAME = "vector_db/ndi_rag_v2_chroma"
COLLECTION_NAME = "ndi_rag_v2"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120


def _load_pdf_documents(pdf_files: list[Path]) -> list[Document]:
    """Loads all pages of every PDF file into LangChain Document objects.

    Args:
        pdf_files: List of PDF file paths to load.

    Returns:
        A list of Document objects, one per PDF page, with source metadata.
    """
    documents: list[Document] = []
    for pdf_file in pdf_files:
        loader = PyPDFLoader(str(pdf_file))
        pages = loader.load()
        for page in pages:
            page.metadata["source_file"] = pdf_file.name
        documents.extend(pages)
    return documents


def _split_documents(documents: list[Document]) -> list[Document]:
    """Splits documents into overlapping text chunks.

    Args:
        documents: List of page-level Document objects.

    Returns:
        A list of chunked Document objects.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def _rebuild_vector_store(
    chunks: list[Document],
    embeddings: HuggingFaceEmbeddings,
    vector_db_dir: Path,
) -> Chroma:
    """Deletes any existing V2 vector store directory and rebuilds it from chunks.

    Args:
        chunks: Chunked Document objects to embed and store.
        embeddings: Embedding model wrapper used by Chroma.
        vector_db_dir: Target directory for the persistent ChromaDB store.

    Returns:
        The newly built Chroma vector store instance.
    """
    if vector_db_dir.exists():
        shutil.rmtree(vector_db_dir)
    vector_db_dir.mkdir(parents=True, exist_ok=True)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(vector_db_dir),
        collection_metadata={"hnsw:space": "cosine"},
    )


def main() -> None:
    """Builds the RAG V2 ChromaDB vector store and prints a build report."""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    project_root = Path(__file__).resolve().parents[2]
    source_dir = project_root / SOURCE_DIR_NAME
    vector_db_dir = project_root / VECTOR_DB_DIR_NAME

    pdf_files = sorted(source_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {source_dir}")
        return

    documents = _load_pdf_documents(pdf_files)
    chunks = _split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    _rebuild_vector_store(chunks, embeddings, vector_db_dir)

    print("RAG V2 Build Report")
    print(f"PDF files found   : {len(pdf_files)}")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    print(f"Pages/documents   : {len(documents)}")
    print(f"Chunks created    : {len(chunks)}")
    print(f"Collection name   : {COLLECTION_NAME}")
    print(f"Vector DB path    : {vector_db_dir}")


if __name__ == "__main__":
    main()
