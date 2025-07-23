# hierarchical/rag/stores/bge_faiss_store.py
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np
from metagpt.logs import logger


class BGEFAISSStore:
    """
    负责FAISS索引的加载、持久化、向量添加与搜索，
    并维护一个从 MinHash 签名到 FAISS 向量ID 的映射。
    """
    def __init__(self, persist_path: str, index_file: str = "bge.faiss", map_file: str = "minhash_to_id.pkl"):
        self.persist_path = Path(persist_path)
        self.index_path = self.persist_path / index_file
        self.map_path = self.persist_path / map_file

        self.faiss_index: Optional[faiss.Index] = None
        self.minhash_to_id: dict[str, int] = {}
        self._load()

    def _load(self):
        logger.info(f"Attempting to load FAISS store from {self.persist_path}")
        if self.index_path.exists() and self.map_path.exists():
            try:
                self.faiss_index = faiss.read_index(str(self.index_path))
                with open(self.map_path, "rb") as f:
                    self.minhash_to_id = pickle.load(f)
                logger.success(f"Successfully loaded FAISS index with {self.faiss_index.ntotal} vectors and map with {len(self.minhash_to_id)} entries.")
            except Exception as e:
                logger.error(f"Failed to load FAISS store from {self.persist_path}: {e}. Initializing new store.")
                self._initialize_empty()
        else:
            logger.warning("FAISS index or map file not found. Initializing a new empty store.")
            self._initialize_empty()

    def _initialize_empty(self):
        self.faiss_index = None
        self.minhash_to_id = {}

    def persist(self):
        if self.faiss_index is None:
            logger.warning("Persist called but FAISS index is not initialized. Nothing to save.")
            return

        self.persist_path.mkdir(parents=True, exist_ok=True)
        try:
            faiss.write_index(self.faiss_index, str(self.index_path))
            with open(self.map_path, "wb") as f:
                pickle.dump(self.minhash_to_id, f)
            logger.success(f"Successfully persisted FAISS store to {self.persist_path}")
        except Exception as e:
            logger.error(f"Failed to persist FAISS store: {e}")

    def add_vector(self, minhash_signature: str, vector: List[float]):
        if minhash_signature in self.minhash_to_id:
            logger.info(f"MinHash signature '{minhash_signature}' already exists in store. Skipping add.")
            return

        np_vector = np.array([vector], dtype=np.float32)
        if self.faiss_index is None:
            dimension = np_vector.shape[1]
            self.faiss_index = faiss.IndexFlatL2(dimension)
            logger.info(f"Initialized new FAISS index with dimension {dimension}.")

        self.faiss_index.add(np_vector)
        vector_id = self.faiss_index.ntotal - 1
        self.minhash_to_id[minhash_signature] = vector_id

    def search(self, minhash_signature: str) -> Optional[np.ndarray]:
        vector_id = self.minhash_to_id.get(minhash_signature)
        if vector_id is not None and self.faiss_index is not None and vector_id < self.faiss_index.ntotal:
            return self.faiss_index.reconstruct(vector_id)
        return None

    def similarity_search(self, query_vector: List[float], k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            return np.array([]), np.array([])

        query_np = np.array([query_vector], dtype=np.float32)
        distances, indices = self.faiss_index.search(query_np, k)
        return distances, indices