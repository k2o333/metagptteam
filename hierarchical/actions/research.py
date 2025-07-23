# hierarchical/actions/research.py (最终更新 - 从 custom_config 获取私有RAG服务配置)
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
from hierarchical.rag.engines.hierarchical_rag_engine import HierarchicalRAGEngine
from hierarchical.rag.adapters.context7_adapter import Context7Adapter
from metagpt.config2 import Config 

class Research(Action):
    """
    一个用于执行研究的Action，它将调用 HierarchicalRAGEngine。
    """
    name: str = "Research"

    def __init__(self, context: Any, **kwargs):
        super().__init__(**kwargs)
        self.context = context
        
        # 【核心修正】: 从 context.kwargs.custom_config 中获取 private_rag_service 配置
        private_rag_config = self.context.kwargs.custom_config.get("private_rag_service", {})
        
        self.context7_adapter = Context7Adapter(
            base_url=private_rag_config.get("base_url", "http://context7.example.com"),
            api_key=private_rag_config.get("api_key", "dummy-api-key")
        )
        self.rag_engine = HierarchicalRAGEngine(config=self.context.config, context7_adapter=self.context7_adapter)
        logger.info("Research Action initialized with HierarchicalRAGEngine.")

    async def run(self, query: str, agent_type: str = "Researcher") -> Dict[str, Any]:
        logger.info(f"Research Action running query: '{query}'")
        rag_response = await self.rag_engine.search(query, agent_type=agent_type)
        logger.info(f"Research Action received RAG response for '{query}'")
        
        return {
            "query": query,
            "response_summary": rag_response.response,
            "retrieved_data": [doc.content for doc in rag_response.rag_context.nodes],
            "extra_info": rag_response.extra_info
        }