
"""Reference clause library.
 
Builds a vector index over the sample NDA corpus in data/raw_pdfs at startup and
exposes similarity search over it, so a flagged clause can be compared against how
standard agreements phrase the same thing.
 
Two deliberate choices:
 
1. Embeddings are computed locally by Chroma's built-in model, not through an API.
   The rest of this app already works without an API key, and a lookup against a
   fixed reference corpus has no reason to depend on one. It also means this feature
   cannot break when a key expires.
 
2. The index is built in memory on first load rather than read from a persisted
   directory. The corpus is small, and rebuilding from the source PDFs keeps the
   index and the documents in the repository from drifting apart.
"""
 
from pathlib import Path
import re
 
import streamlit as st
 
PDF_DIR = Path("data/raw_pdfs")
MIN_CHARS = 180      # shorter fragments are headings or signature lines
MAX_CHARS = 1500     # longer ones get truncated so one clause cannot dominate
 
 
def _split_clauses(text: str):
    """Split on numbered clause headings, falling back to blank-line paragraphs."""
    pattern = re.compile(r"^\s*(\d+(\.\d+)*)(\.|\))?\s", re.MULTILINE)
 
    if pattern.search(text):
        pieces, current = [], []
        for line in text.splitlines():
            if pattern.match(line) and current:
                pieces.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            pieces.append("\n".join(current))
    else:
        pieces = re.split(r"\n\s*\n", text)
 
    for piece in pieces:
        cleaned = " ".join(piece.split())
        if len(cleaned) >= MIN_CHARS:
            yield cleaned[:MAX_CHARS]
 
 
@st.cache_resource(show_spinner=False)
def load_library():
    """Return the reference collection, or None if the corpus is unavailable."""
    import chromadb
    from chromadb.utils import embedding_functions
    import pdfplumber
 
    if not PDF_DIR.exists():
        return None
 
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name="nda_reference",
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )
 
    documents, metadatas, ids = [], [], []
    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            continue
        for i, chunk in enumerate(_split_clauses(text)):
            documents.append(chunk)
            metadatas.append({"source": pdf_path.stem})
            ids.append(f"{pdf_path.stem}-{i}")
 
    if not documents:
        return None
 
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    return collection
 
 
def search_similar_clauses(text: str, n_results: int = 3):
    """Return reference clauses closest to the given text.
 
    Returns an empty list if the library could not be built - the caller should
    treat this feature as optional and carry on without it.
    """
    try:
        collection = load_library()
        if collection is None:
            return []
        results = collection.query(query_texts=[text], n_results=n_results)
    except Exception:
        return []
 
    out = []
    for doc, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        out.append({
            "text": doc,
            "source": meta.get("source", "reference"),
            "similarity": max(0.0, 1.0 - distance / 2.0),
        })
    return out
 











