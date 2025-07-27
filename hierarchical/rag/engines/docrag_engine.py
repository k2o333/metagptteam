# mghier/hierarchical/rag/engines/docrag_engine.py (阶段一最终修复版)

from __future__ import annotations
import asyncio
from pathlib import Path
from typing import List

from llama_index.core.schema import Document, NodeWithScore
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.schema import (
    FAISSIndexConfig,
    FAISSRetrieverConfig,
)

class DocRAGEngine:
    """
    一个可持久化的知识库引擎，封装了MetaGPT的SimpleEngine。
    它专注于提供面向文档存储、增删和清理的高级接口。
    注意：此类应通过异步工厂方法 from_path() 进行实例化。
    """
    
    def __init__(self, persist_path: str, rag_engine: SimpleEngine):
        self.persist_path = Path(persist_path)
        self.rag_engine = rag_engine

    @classmethod
    async def from_path(cls, persist_path: str) -> DocRAGEngine:
        """
        异步工厂方法，用于创建或加载 DocRAGEngine 实例。
        """
        path_obj = Path(persist_path)
        rag_engine: SimpleEngine

        if (path_obj / "default__vector_store.json").exists():
            logger.info(f"Loading existing DocRAGEngine from {path_obj}...")
            index_config = FAISSIndexConfig(persist_path=str(path_obj))
            
            # 【关键修复】确保在加载时也使用 FAISSRetrieverConfig 来获得正确的、可修改的检索器类型
            rag_engine = SimpleEngine.from_index(
                index_config=index_config,
                retriever_configs=[FAISSRetrieverConfig()]
            )
        else:
            logger.info(f"Creating new DocRAGEngine at {path_obj}...")
            path_obj.mkdir(parents=True, exist_ok=True)
            rag_engine = SimpleEngine.from_objs(
                [],
                retriever_configs=[FAISSRetrieverConfig()]
            )
            temp_instance_for_persist = cls(persist_path, rag_engine)
            await temp_instance_for_persist.persist()
            
        return cls(persist_path, rag_engine)

    async def add_texts(self, texts: list[str], metadatas: list[dict] | None = None):
        """
        向知识库中添加新的文本文档。
        """
        if not texts:
            return
        
        if metadatas and len(texts) != len(metadatas):
            raise ValueError("The number of texts must match the number of metadatas.")

        documents = [
            Document(text=t, metadata=m or {}) 
            for t, m in zip(texts, metadatas or [None] * len(texts))
        ]
        
        # 现在 retriever 必定是 FAISSRetriever，所以它有 add_nodes 方法
        self.rag_engine.retriever.add_nodes(documents)
        logger.info(f"Added {len(documents)} new documents to the RAG engine via retriever.")
        
        await self.persist()

    async def persist(self):
        """
        将当前RAG引擎的状态（包括新添加的文档）保存到磁盘。
        """
        retriever = self.rag_engine.retriever
        if isinstance(retriever, FAISSRetriever) and hasattr(retriever, 'persist'):
            retriever.persist(persist_dir=str(self.persist_path))
            logger.success(f"DocRAGEngine state persisted to {self.persist_path}")
        else:
            if hasattr(self.rag_engine, 'persist'):
                self.rag_engine.persist(persist_dir=str(self.persist_path))
                logger.success(f"DocRAGEngine state persisted via engine.persist to {self.persist_path}")
            else: 
                self.rag_engine.storage_context.persist(persist_dir=str(self.persist_path))
                logger.success(f"DocRAGEngine state persisted via storage_context to {self.persist_path}")

    async def asearch(self, query: str, top_k: int = 3) -> List[NodeWithScore]:
        """
        在知识库中进行异步相似度搜索。
        """
        if hasattr(self.rag_engine.retriever, 'similarity_top_k'):
            self.rag_engine.retriever.similarity_top_k = top_k
        retrieved_nodes = await self.rag_engine.aretrieve(query)
        logger.info(f"Retrieved {len(retrieved_nodes)} nodes for query: '{query}'")
        return retrieved_nodes