# my_private_rag_service/rag_backend.py (最终修正，从 custom_config 获取私有RAG服务配置)
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import yaml # 【新增】导入 yaml

import numpy as np
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Document, Settings
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from metagpt.config2 import Config

# --- 显式添加 hierarchical 项目根目录到 sys.path ---
current_file_path = Path(__file__).resolve()
mghier_root = current_file_path.parent.parent
sys.path.insert(0, str(mghier_root))
# --------------------------------------------------------------------

from hierarchical.rag.stores.bge_faiss_store import BGEFAISSStore

class RAGSystem:
    def __init__(self, config_path: str = "/root/.metagpt/config2.yaml"):
        # 【修正】: 加载MetaGPT的标准Config
        self.config = Config.from_yaml_file(Path(config_path)) 
        
        # 【核心修正】: 直接从原始YAML数据中提取 private_rag_service 配置
        # 因为 Config 对象本身可能没有这个属性
        raw_config_data: Dict[str, Any] = {}
        with open(Path(config_path), 'r', encoding='utf-8') as f:
            raw_config_data = yaml.safe_load(f)
        
        private_rag_service_config = raw_config_data.get("private_rag_service", {})
        
        # 初始化嵌入模型 (这部分保持不变，因为 embedding 是 Config 的标准字段)
        self.embedding_model = RAGEmbeddingFactory(config=self.config).get_rag_embedding()
        
        # 初始化向量存储
        # 【修正】: 使用从原始YAML中获取的 private_rag_service_config
        persist_path = private_rag_service_config.get("persist_path", "./data") 
        
        Path(persist_path).mkdir(parents=True, exist_ok=True) # 确保持久化目录存在

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
                    "id": idx,
                    "distance": float(distances[0][i]),
                    "content": f"Retrieved content for ID {idx} (Distance: {distances[0][i]:.4f}). [Placeholder]"
                })
        return results