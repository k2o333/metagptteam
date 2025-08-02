# my_private_rag_service/prepare_data.py
import os
from rag_backend import RAGSystem

if __name__ == "__main__":
    print("Initializing RAGSystem to prepare/load data...")
    # 这将触发RAGSystem的__init__方法，如果索引不存在，会创建并持久化示例数据
    rag_system = RAGSystem(config_path="/root/.metagpt/config2.yaml")
    print("RAG data prepared/loaded successfully.")
    print(f"FAISS index located at {rag_system.vector_store.index_path}")
    print(f"MinHash map located at {rag_system.vector_store.map_path}")