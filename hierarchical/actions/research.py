# hierarchical/actions/research.py
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
from hierarchical.rag.engines.hierarchical_rag_engine import HierarchicalRAGEngine
from hierarchical.rag.adapters.context7_adapter import Context7Adapter
from hierarchical.schemas import RAGResponse

class Research(Action):
    """
    一个用于执行研究的Action，它将调用 HierarchicalRAGEngine。
    """
    name: str = "Research"

    def __init__(self, context: Any, **kwargs):
        """
        初始化 Research Action。
        
        注意：此 Action 依赖于运行时传入的 `context` 对象来初始化其 RAG 引擎，
        因为它需要访问全局配置和我们自定义的服务配置。
        """
        super().__init__(**kwargs)
        self.context = context
        
        # 从 context.kwargs.custom_config 中获取 private_rag_service 配置
        custom_config = self.context.kwargs.get("custom_config", {})
        private_rag_config = custom_config.get("private_rag_service", {})
        
        self.context7_adapter = Context7Adapter(
            base_url=private_rag_config.get("base_url", "http://localhost:9000"),
            api_key=private_rag_config.get("api_key", "dummy-api-key")
        )
        self.rag_engine = HierarchicalRAGEngine(
            config=self.context.config, 
            context7_adapter=self.context7_adapter
        )
        logger.info("Research Action initialized with HierarchicalRAGEngine.")

    async def run(self, query: str, agent_type: str = "Researcher") -> Dict[str, Any]:
        """
        执行研究查询。
        :param query: 研究查询字符串。
        :param agent_type: 发起查询的代理类型。
        :return: 研究结果字典。
        """
        logger.info(f"Research Action running query: '{query}'")
        rag_response: RAGResponse = await self.rag_engine.search(query, agent_type=agent_type)
        logger.info(f"Research Action received RAG response for '{query}'")
        
        # 从 rag_response.rag_context.nodes 属性获取检索到的内容
        # 即使 RAGContext 内部使用 _nodes，我们通过 @property 访问它
        return {
            "query": query,
            "response_summary": rag_response.response,
            "retrieved_data": [node.get_content() for node in rag_response.rag_context.nodes],
            "extra_info": rag_response.extra_info
        }