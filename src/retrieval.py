"""
Local Semantic Retrieval Pipeline for RetailMind AI.
Uses gemini-embedding-001 representation with local numpy cosine similarity search.
Stores embeddings locally in data/embeddings/ — ZERO hosted vector databases.
Precomputes embeddings for fast, deterministic startup.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

logger = logging.getLogger("RetailMind.Retrieval")

EMBEDDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "embeddings")
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

class LocalRetrievalPipeline:
    def __init__(self, data_dir: Optional[str] = None):
        self.embeddings_dir = EMBEDDINGS_DIR
        self.metadata_file = os.path.join(self.embeddings_dir, "metadata.json")
        self.embeddings_file = os.path.join(self.embeddings_dir, "embeddings.npy")
        
        self.metadata: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.vocab: Dict[str, int] = {}
        
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.has_gemini = bool(self.gemini_key and self.gemini_key != "your_gemini_api_key_here")

        # Load or initialize precomputed vector store
        self.load_or_build_index()

    def build_corpus_documents(self) -> List[Dict[str, Any]]:
        """Extracts structured descriptions from retail CSVs."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prod_path = os.path.join(base_dir, "data", "products.csv")
        stores_path = os.path.join(base_dir, "data", "stores.csv")

        docs = []

        # Product documents
        if os.path.exists(prod_path):
            df_prods = pd.read_csv(prod_path)
            for _, r in df_prods.iterrows():
                text = (
                    f"Product {r['product_name']} (SKU: {r['product_id']}). "
                    f"Category: {r['category']}. Selling Price: ₹{r['selling_price']}, "
                    f"Cost Price: ₹{r['cost_price']}. Reorder Threshold: {r['reorder_level']} units. "
                    f"Supplier: {r['supplier']}."
                )
                docs.append({
                    "id": f"prod_{r['product_id']}",
                    "type": "product",
                    "product_id": r["product_id"],
                    "product_name": r["product_name"],
                    "category": r["category"],
                    "text": text
                })

        # Store documents
        if os.path.exists(stores_path):
            df_stores = pd.read_csv(stores_path)
            for _, r in df_stores.iterrows():
                text = (
                    f"Store {r['store_name']} (ID: {r['store_id']}). "
                    f"Physical Location: {r['location']}. Retail format: Flagship and regional hub."
                )
                docs.append({
                    "id": f"store_{r['store_id']}",
                    "type": "store",
                    "store_id": r["store_id"],
                    "store_name": r["store_name"],
                    "text": text
                })

        # Operational concept documents for retail queries
        concepts = [
            {"id": "concept_stockout", "type": "concept", "concept": "stockout", "text": "Stock-out risk, low inventory, running out, depleted stock, urgent reorder, days of inventory remaining under 7 days."},
            {"id": "concept_overstock", "type": "concept", "concept": "overstock", "text": "Overstocked inventory, excess stock, surplus items, days of inventory exceeding 45 days, tied up working capital."},
            {"id": "concept_slow", "type": "concept", "concept": "slow_moving", "text": "Slow moving products, low velocity, stagnant stock, dead inventory, unsold items over 60 days."},
            {"id": "concept_spike", "type": "concept", "concept": "sales_spike", "text": "Sales spike, sales surge, demand increase, recent sales jump over 40% vs baseline."},
            {"id": "concept_drop", "type": "concept", "concept": "sales_drop", "text": "Sales drop, declining sales, decreased revenue, falling volume over 30% decline."},
            {"id": "concept_attention", "type": "concept", "concept": "attention_today", "text": "What needs attention today, critical daily flags, manager checklist, urgent tasks."}
        ]
        docs.extend(concepts)

        return docs

    def _generate_deterministic_vector(self, text: str, dim: int = 256) -> np.ndarray:
        """
        Creates a normalized pseudo-semantic vector representation based on
        character n-grams and term frequencies. Used for local zero-dependency offline embedding.
        """
        tokens = text.lower().replace(",", " ").replace(".", " ").replace("₹", " ").split()
        vec = np.zeros(dim, dtype=np.float32)
        for t in tokens:
            h = hash(t) % dim
            vec[h] += 1.0
            # Also hash 3-grams
            if len(t) >= 3:
                for i in range(len(t) - 2):
                    g = hash(t[i:i+3]) % dim
                    vec[g] += 0.5
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def build_and_save_index(self):
        """Builds and caches precomputed vector embeddings locally."""
        docs = self.build_corpus_documents()
        vectors = []

        # Try gemini-embedding-001 if API key is provided, else fallback to deterministic semantic vector
        use_gemini_api = False
        if self.has_gemini:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                for doc in docs:
                    res = genai.embed_content(
                        model="models/gemini-embedding-001",
                        content=doc["text"],
                        task_type="retrieval_document"
                    )
                    v = np.array(res["embedding"], dtype=np.float32)
                    v /= (np.linalg.norm(v) + 1e-9)
                    vectors.append(v)
                use_gemini_api = True
                logger.info("Successfully generated embeddings via gemini-embedding-001.")
            except Exception as e:
                logger.warning(f"Failed to use gemini-embedding-001 API ({e}). Using deterministic offline embeddings.")
                vectors = []

        if not use_gemini_api:
            for doc in docs:
                v = self._generate_deterministic_vector(doc["text"], dim=256)
                vectors.append(v)

        self.embeddings = np.array(vectors, dtype=np.float32)
        self.metadata = docs

        # Save to disk
        np.save(self.embeddings_file, self.embeddings)
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved {len(docs)} embeddings to {self.embeddings_dir}")

    def load_or_build_index(self):
        """Loads index from disk or generates it if missing."""
        if os.path.exists(self.embeddings_file) and os.path.exists(self.metadata_file):
            try:
                self.embeddings = np.load(self.embeddings_file)
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded {len(self.metadata)} embeddings from disk cache.")
                return
            except Exception as e:
                logger.warning(f"Error reading embedding cache: {e}. Rebuilding...")

        self.build_and_save_index()

    def get_query_embedding(self, query: str) -> np.ndarray:
        """Generates embedding for incoming query."""
        if self.has_gemini:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                res = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=query,
                    task_type="retrieval_query"
                )
                v = np.array(res["embedding"], dtype=np.float32)
                v /= (np.linalg.norm(v) + 1e-9)
                if self.embeddings is not None and v.shape[0] == self.embeddings.shape[1]:
                    return v
            except Exception as e:
                logger.warning(f"Query embedding API failed: {e}. Falling back to deterministic embedding.")

        # Fallback to deterministic vector
        dim = self.embeddings.shape[1] if self.embeddings is not None else 256
        return self._generate_deterministic_vector(query, dim=dim)

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Calculates local numpy cosine similarity between query and stored documents.
        Returns top_k most relevant items.
        """
        if self.embeddings is None or len(self.metadata) == 0:
            return []

        q_vec = self.get_query_embedding(query)
        # Cosine similarity using dot product (vectors are normalized)
        scores = np.dot(self.embeddings, q_vec)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            doc = dict(self.metadata[idx])
            doc["similarity_score"] = round(float(scores[idx]), 4)
            results.append(doc)

        return results
