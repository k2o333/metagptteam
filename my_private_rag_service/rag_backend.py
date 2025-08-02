# my_private_rag_service/rag_backend.py (最终修正版)
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import yaml

import numpy as np
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from metagpt.config2 import Config

current_file_path = Path(__file__).resolve()
mghier_root = current_file_path.parent.parent
sys.path.insert(0, str(mghier_root))

from hierarchical.rag.stores.bge_faiss_store import BGEFAISSStore

class RAGSystem:
    def __init__(self, config_path: str = "/root/.metagpt/config2.yaml"):
        self.config = Config.from_yaml_file(Path(config_path))
        
        raw_config_data: Dict[str, Any] = {}
        with open(Path(config_path), 'r', encoding='utf-8') as f:
            raw_config_data = yaml.safe_load(f)
        
        private_rag_service_config = raw_config_data.get("private_rag_service", {})
        
        self.embedding_model = RAGEmbeddingFactory(config=self.config).get_rag_embedding()
        
        persist_path = private_rag_service_config.get("persist_path", "./data")
        Path(persist_path).mkdir(parents=True, exist_ok=True)
        self.vector_store = BGEFAISSStore(persist_path=persist_path)
        
        if self.vector_store.faiss_index is None or self.vector_store.faiss_index.ntotal == 0:
            print("FAISS index is empty or not loaded, initializing with sample data.")
            sample_texts = [
                "RAG系统结合了检索和生成，提高了LLM的事实准确性。",
                "MinHash是一种局部敏感哈希技术，用于估计集合的相似度。",
                "FAISS是一个用于高效相似度搜索和聚类的库。",
                "BGE-large-zh-v1.5是中文文本嵌入模型，广泛用于RAG。",
                "人工智能在教育领域可以个性化学习路径，提供智能辅导。"
            ]
            for i, text in enumerate(sample_texts):
                embedding = self.embedding_model.get_text_embedding(text)
                self.vector_store.add_vector(f"doc_{i}", embedding)
            self.vector_store.persist()
            print(f"Added {len(sample_texts)} sample documents to FAISS.")

    async def query(self, text: str) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_model.get_text_embedding(text)
        distances, indices = self.vector_store.similarity_search(query_embedding, k=2)

        results = []
        if indices.size > 0:
            for i, idx in enumerate(indices[0]):
                results.append({
                    # 【核心修正】: 将 numpy 类型转换为 Python 原生类型
                    "id": int(idx),
                    "distance": float(distances[0][i]),
                    "content": f"Retrieved content for ID {int(idx)} (Distance: {float(distances[0][i]):.4f}). [Placeholder]"
                })
        return results