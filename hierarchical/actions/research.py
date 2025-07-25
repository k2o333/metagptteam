# mghier/hierarchical/actions/research.py (完整重构版)

import sys
from pathlib import Path
from typing import Dict, Any

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.config2 import Config

# 导入我们新的 DocRAGEngine
from hierarchical.rag.engines.docrag_engine import DocRAGEngine 
from hierarchical.schemas import RAGResponse

class Research(Action):
    """
    一个用于执行研究的Action。
    在当前版本中，它将调用本地的 DocRAGEngine。
    """
    name: str = "Research"

    def __init__(self, context: Any, **kwargs):
        """
        初始化 Research Action。
        
        注意：此 Action 依赖于运行时传入的 `context` 对象来初始化其 RAG 引擎，
        因为它需要访问全局配置。
        """
        super().__init__(**kwargs)
        self.context = context
        
        # 实例化我们新的、干净的 DocRAGEngine
        self.rag_engine = DocRAGEngine(config=self.context.config)
        logger.info("Research Action initialized with DocRAGEngine.")

    async def run(self, query: str, agent_type: str = "Researcher") -> Dict[str, Any]:
        """
        执行研究查询，当前仅使用本地RAG。

        :param query: 研究查询字符串。
        :param agent_type: 发起查询的代理类型 (当前未使用，为保持签名兼容性保留)。
        :return: 研究结果字典。
        """
        logger.info(f"Research Action running query: '{query}' using local DocRAG.")
        
        # 直接调用我们本地引擎的 search 方法
        rag_response: RAGResponse = await self.rag_engine.search(query)
        logger.info(f"Research Action received DocRAG response for '{query}'")
        
        # 从 rag_response.rag_context.nodes 属性获取检索到的内容
        return {
            "query": query,
            "response_summary": rag_response.response,
            "retrieved_data": [node.get_content() for node in rag_response.rag_context.nodes],
            "extra_info": rag_response.extra_info
        }