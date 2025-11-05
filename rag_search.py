# rag_search.py

import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

embedder = embedding_functions.OpenAIEmbeddingFunction(
    api_key=api_key,
    model_name="text-embedding-3-small"
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="nda_corpus",
    embedding_function=embedder
)

def search_similar_clauses(text, n_results=3):
    """
    输入：一段合同条款文本
    输出：向量 DB 中最相似的参考条款（3 条）
    """
    results = collection.query(
        query_texts=[text],
        n_results=n_results
    )

    documents = results["documents"][0]
    sources = results["metadatas"][0]

    formatted = []
    for doc, meta in zip(documents, sources):
        formatted.append(f"- **Source:** {meta['source']}\n  {doc.strip()}\n")

    return "\n".join(formatted)