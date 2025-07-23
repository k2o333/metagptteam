# hierarchical/rag/adapters/context7_adapter.py (新建)
from typing import Any, Dict, Optional

import requests
from metagpt.logs import logger

class Context7Adapter:
    """
    封装与Context7 MCP（多内容处理）平台的所有交互逻辑。
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        """
        初始化适配器。

        :param base_url: Context7 API的基础URL (例如: "http://context7.example.com")。
        :param api_key: 用于认证的API密钥。
        :param timeout: 请求超时时间（秒）。
        """
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def query(self, query: str, agent_type: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        向Context7发送一个查询请求。

        :param query: 查询字符串。
        :param agent_type: 调用此查询的代理类型 (例如: "Writer", "Reviewer")。
        :param params: 其他特定于查询的参数。
        :return: 来自API的JSON响应字典，或在失败时返回一个fallback字典。
        """
        url = f"{self.base_url}api/v1/query"
        payload = {
            "query": query,
            "agentType": agent_type,
            "params": params or {},
        }
        
        logger.info(f"Querying Context7: {url} with agent_type: {agent_type}")
        
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()  # 如果状态码是4xx或5xx，则抛出HTTPError
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Context7 query failed due to a network error: {e}. Triggering fallback.")
            return self._fallback_search(query)

    def audit_query(self, query: str, agent_type: str) -> bool:
        """
        发送一个用于审计目的的查询（通常是fire-and-forget）。

        :param query: 被审计的查询字符串。
        :param agent_type: 执行查询的代理类型。
        :return: 如果审计日志发送成功，则为True，否则为False。
        """
        url = f"{self.base_url}api/v1/audit"
        payload = {"query": query, "agentType": agent_type}
        
        try:
            response = self.session.post(url, json=payload, timeout=5) # 使用较短的超时
            response.raise_for_status()
            logger.info(f"Successfully audited query for agent: {agent_type}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send audit log to Context7: {e}")
            return False

    def _fallback_search(self, query: str) -> Dict[str, Any]:
        """
        在主查询失败时提供一个标准的、安全的降级响应。

        :param query: 原始查询。
        :return: 一个表示失败和降级的字典。
        """
        return {
            "status": "error",
            "message": "Context7 search failed, fallback mechanism activated.",
            "data": [],
            "original_query": query,
        }