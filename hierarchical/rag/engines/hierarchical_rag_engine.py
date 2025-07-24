# hierarchical/rag/engines/hierarchical_rag_engine.py (最终修正版)
import json
from typing import Any, Dict, List

from metagpt.rag.interface import RAGObject
from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from metagpt.rag.schema import FAISSRetrieverConfig, LLMRankerConfig
from hierarchical.schemas import RAGContext, RAGResponse
from hierarchical.rag.adapters.context7_adapter import Context7Adapter
from hierarchical.rag.utils.hashing import generate_minhash_signature, semantic_fingerprint

class TextObject(RAGObject):
    """A simple text object that implements the RAGObject protocol."""
    def __init__(self, text: str):
        self.text = text

    def rag_key(self) -> str:
        return self.text
    
    def model_dump_json(self) -> str:
        return json.dumps({"text": self.text})

class HierarchicalRAGEngine:
    """
    增强型RAG引擎，集成外部数据源和语义指纹。
    """
    def __init__(self, config: Config, context7_adapter: Context7Adapter):
        self.config = config
        self.context7_adapter = context7_adapter
        self.embedding_model = RAGEmbeddingFactory(config=config).get_rag_embedding()
        self.rag_engine: SimpleEngine = self._initialize_rag_engine()
        logger.info("HierarchicalRAGEngine initialized.")

    def _initialize_rag_engine(self) -> SimpleEngine:
        """
        初始化RAG引擎。
        """
        # 【核心修正】: 不再手动指定 dimensions。
        # FAISSRetrieverConfig 会根据全局 config.embedding.dimensions 自动设置。
        retriever_configs = [FAISSRetrieverConfig(similarity_top_k=2)]
        ranker_configs = [LLMRankerConfig()]
        
        texts = [
            "示例文档1：RAG系统是检索增强生成。", 
            "示例文档2：MinHash用于集合相似度。", 
            "示例文档3：FAISS是高效相似度搜索库。"
        ]
        rag_objects = [TextObject(text=t) for t in texts]
        
        return SimpleEngine.from_objs(
            objs=rag_objects,
            retriever_configs=retriever_configs,
            ranker_configs=ranker_configs,
            embed_model=self.embedding_model
        )

    async def search(self, query: str, agent_type: str = "General") -> RAGResponse:
        """
        执行增强型RAG搜索。
        """
        logger.info(f"HierarchicalRAGEngine performing search for: {query}")
        
        # 1. 查询私有RAG服务
        logger.info(f"Querying private RAG service via custom adapter...")
        private_rag_results = self.context7_adapter.query(query, agent_type)
        context_data = private_rag_results.get("data", [])
        
        # 2. 使用本地RAG引擎检索
        retrieved_nodes = await self.rag_engine.aretrieve(query)
        
        # 3. 构建 RAGContext
        rag_context = RAGContext(nodes=retrieved_nodes, raw_data=context_data)

        # 4. 生成语义指纹
        query_embedding = self.embedding_model.get_text_embedding(query)
        minhash_fp = generate_minhash_signature(query)
        semantic_fp = semantic_fingerprint(query_embedding)
        logger.debug(f"Query '{query}' MinHash: {minhash_fp}, Semantic FP: {semantic_fp}")

        # 5. 构建 RAGResponse
        response = RAGResponse(
            query=query,
            rag_context=rag_context,
            response="Placeholder RAG response based on internal docs and Private RAG Service data.",
            extra_info={
                "private_rag_status": private_rag_results.get("status"),
                "minhash_signature": minhash_fp,
                "semantic_fingerprint": semantic_fp,
            }
        )
        return response