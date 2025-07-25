# mghier/hierarchical/rag/engines/docrag_engine.py (完整重构版)

import json
from typing import List

from metagpt.rag.interface import RAGObject
from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from metagpt.rag.schema import FAISSRetrieverConfig, LLMRankerConfig
from hierarchical.schemas import RAGContext, RAGResponse

class TextObject(RAGObject):
    """A simple text object that implements the RAGObject protocol."""
    def __init__(self, text: str):
        self.text = text

    def rag_key(self) -> str:
        return self.text
    
    def model_dump_json(self) -> str:
        return json.dumps({"text": self.text})

class DocRAGEngine:
    """
    一个纯粹的本地文档RAG引擎，使用FAISS进行内部检索。
    """
    def __init__(self, config: Config):
        """
        初始化 DocRAGEngine。
        :param config: 全局配置对象，用于初始化嵌入模型。
        """
        self.config = config
        self.embedding_model = RAGEmbeddingFactory(config=config).get_rag_embedding()
        self.rag_engine: SimpleEngine = self._initialize_rag_engine()
        logger.info("DocRAGEngine (Local RAG) initialized.")

    def _initialize_rag_engine(self) -> SimpleEngine:
        """
        初始化内部的 SimpleEngine，并加载一些示例数据。
        """
        retriever_configs = [FAISSRetrieverConfig(similarity_top_k=2)]
        ranker_configs = [LLMRankerConfig()]
        
        texts = [
            "示例文档1：DocRAG系统是纯本地的检索增强生成。", 
            "示例文档2：它使用FAISS在内存中进行相似度搜索。", 
            "示例文档3：这个引擎不进行任何外部网络调用。"
        ]
        rag_objects = [TextObject(text=t) for t in texts]
        
        logger.info("Initializing SimpleEngine with sample local documents.")
        return SimpleEngine.from_objs(
            objs=rag_objects,
            retriever_configs=retriever_configs,
            ranker_configs=ranker_configs,
            embed_model=self.embedding_model
        )

    async def search(self, query: str) -> RAGResponse:
        """
        执行纯粹的本地RAG搜索。
        
        :param query: 搜索查询字符串。
        :return: 包含本地检索结果的 RAGResponse 对象。
        """
        logger.info(f"DocRAGEngine performing local search for: '{query}'")
        
        # 1. 直接使用本地RAG引擎检索
        retrieved_nodes = await self.rag_engine.aretrieve(query)
        logger.info(f"DocRAGEngine retrieved {len(retrieved_nodes)} nodes locally.")
        
        # 2. 构建 RAGContext
        # raw_data 为空，因为没有外部数据源
        rag_context = RAGContext(nodes=retrieved_nodes, raw_data=[]) 

        # 3. 构建 RAGResponse
        response = RAGResponse(
            query=query,
            rag_context=rag_context,
            response="Placeholder response based on locally retrieved documents.",
            extra_info={
                "source": "docrag_local_engine" # 明确来源
            }
        )
        return response