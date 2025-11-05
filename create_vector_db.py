#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not set. Add it to .env and run `source .env`.")

# ✅ Use Chroma's built-in OpenAI embedding wrapper
embedder = embedding_functions.OpenAIEmbeddingFunction(
    api_key=api_key,
    model_name="text-embedding-3-small"  # 💡 stable & cheap
)

# Create / load vector DB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="nda_corpus",
    embedding_function=embedder    # ✅ Correct
)

# Load text files
TXT_DIR = Path("data/txt")
txt_files = list(TXT_DIR.glob("*.txt"))
if not txt_files:
    raise FileNotFoundError("❌ No .txt files found in data/txt — run extract_pdfs.py first.")

print(f"\n📁 Found {len(txt_files)} NDA text files. Starting embedding...\n")

for f in txt_files:
    text = f.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        print(f"⚠️ Skipping empty file: {f.name}")
        continue

    # Chunk text every ~400 chars (safe average for legal contracts)
    chunks = [text[i:i+400] for i in range(0, len(text), 400)]

    ids = [f"{f.stem}_{i}" for i in range(len(chunks))]
    metadata = [{"source": f.name} for _ in chunks]

    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadata
    )

    print(f"✅ Embedded {len(chunks)} chunks from {f.name}")

print("\n🎉 DONE — Vector Database is ready at ./chroma_db\n")