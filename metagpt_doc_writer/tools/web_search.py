# /root/metagpt/mgfr/metagpt_doc_writer/tools/web_search.py (最终修复版)

from pydantic import BaseModel, Field
from metagpt.tools.search_engine import SearchEngine
from metagpt.configs.search_config import SearchConfig
from .base_tool import BaseTool, ToolSchema

class WebSearchParams(BaseModel):
    query: str = Field(..., description="The search query string")

class WebSearch(BaseTool):
    """A wrapper for MetaGPT's SearchEngine."""
    engine: SearchEngine

    def __init__(self, search_config: SearchConfig = None):
        """
        Initializes the WebSearch tool.
        Args:
            search_config: A SearchConfig object. If None, a default DDG engine is created.
        """
        if not search_config or not search_config.api_type:
            effective_config = SearchConfig(api_type="ddg")
        else:
            effective_config = search_config
        
        # 关键修复：在创建 SearchEngine 时，明确地将配置中的 api_type 传递给 engine 参数
        self.engine = SearchEngine(
            config=effective_config,
            engine=effective_config.api_type  # <--- 新增这行
        )

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="web_search",
            description="Searches the web for a given query and returns the top results.",
            parameters=WebSearchParams
        )

    async def run(self, query: str) -> str:
        results = await self.engine.run(query)
        return str(results)