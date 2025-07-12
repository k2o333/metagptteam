# 文件路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/performance_monitor.py (最终修正版 V4)

from collections import defaultdict
import datetime
from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger

class PerformanceMonitor(DocWriterBaseRole):
    name: str = "PerformanceMonitor"
    profile: str = "Performance Monitor"
    goal: str = "Monitor the performance of the team and report on it"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([]) # 没有可供LLM选择的行动
        self._watch({Message}) # 监听所有类型的消息

        self._action_stats = defaultdict(lambda: {
            'calls': 0, 'total_tokens': 0, 'total_cost_usd': 0.0, 'total_execution_time_seconds': 0.0
        })
        self._overall_stats = {
            'total_llm_tokens': 0, 'total_llm_cost_usd': 0.0, 'total_execution_time_seconds': 0.0
        }
        # 因为它不产生新消息，所以不需要react_mode
        self.rc.react_mode = "inaction" 

    async def _observe(self) -> int:
        """
        【核心修正】: 遵循基类无参签名。在内部处理所有新消息。
        """
        # 调用父类的_observe，它会把新消息填充到 self.rc.news
        await super()._observe()
        
        # 遍历所有新观察到的消息
        for msg in self.rc.news:
            if not msg or not msg.cause_by:
                continue

            cost = msg.cost if hasattr(msg, 'cost') else 0.0
            token_usage = msg.token_usage or {}
            tokens = token_usage.get('prompt_tokens', 0) + token_usage.get('completion_tokens', 0)

            execution_time = 0.0
            if hasattr(msg, 'sent_time') and hasattr(msg, 'recv_time') and msg.sent_time and msg.recv_time:
                try:
                    sent = datetime.datetime.fromtimestamp(msg.sent_time) if isinstance(msg.sent_time, (int, float)) else msg.sent_time
                    recv = datetime.datetime.fromtimestamp(msg.recv_time) if isinstance(msg.recv_time, (int, float)) else msg.recv_time
                    execution_time = abs((sent - recv).total_seconds())
                except Exception:
                    pass

            action_name = msg.cause_by if isinstance(msg.cause_by, str) else msg.cause_by.__name__

            stats = self._action_stats[action_name]
            stats['calls'] += 1
            stats['total_execution_time_seconds'] += execution_time

            if tokens > 0 or cost > 0:
                stats['total_tokens'] += tokens
                stats['total_cost_usd'] += cost
                self._overall_stats['total_llm_tokens'] += tokens
                self._overall_stats['total_llm_cost_usd'] += cost

            self._overall_stats['total_execution_time_seconds'] += execution_time
        
        # 返回观察到的消息数量，但不触发行动
        return 0

    async def _act(self) -> Message:
        # 这个角色只观察，不主动行动
        return None

    def get_performance_report(self) -> dict:
        report = {'overall': self._overall_stats.copy(), 'by_action': {}}
        for action, stats in self._action_stats.items():
            report['by_action'][action] = {
                'calls': stats['calls'], 'total_tokens': stats['total_tokens'],
                'total_cost_usd': round(stats['total_cost_usd'], 6),
                'total_execution_time_seconds': round(stats['total_execution_time_seconds'], 2),
                'average_tokens_per_call': round(stats['total_tokens'] / stats['calls']) if stats['calls'] > 0 else 0,
                'average_cost_per_call_usd': round(stats['total_cost_usd'] / stats['calls'], 6) if stats['calls'] > 0 else 0,
                'average_execution_time_seconds': round(stats['total_execution_time_seconds'] / stats['calls'], 2) if stats['calls'] > 0 else 0
            }
        return report