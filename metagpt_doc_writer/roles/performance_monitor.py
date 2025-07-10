# /root/metagpt/mgfr/metagpt_doc_writer/roles/performance_monitor.py

from collections import defaultdict
import datetime
from .base_role import MyBaseRole
from metagpt.schema import Message
# FIX: The 'Costs' class has been removed in newer versions. We will work directly
# with attributes from the Message object, so no special import is needed here.

class PerformanceMonitor(MyBaseRole):
    name: str = "PerformanceMonitor"
    profile: str = "Performance Monitor"
    goal: str = "Monitor the performance of the team and report on it"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])  # Non-LLM role
        self._action_stats = defaultdict(lambda: {
            'calls': 0,
            'total_tokens': 0,
            'total_cost_usd': 0.0,
            'total_execution_time_seconds': 0.0
        })
        self._overall_stats = {
            'total_llm_tokens': 0,
            'total_llm_cost_usd': 0.0,
            'total_execution_time_seconds': 0.0
        }

    # FIX: The signature is made compatible and the logic is updated to use new Message attributes.
    async def _observe(self, msg: Message = None) -> None:
        if not msg or not msg.cause_by:
            return

        # FIX: Access cost and token usage directly from the message object.
        cost = msg.cost  # This is a float representing the dollar cost.
        token_usage = msg.token_usage or {}  # This is a dict, e.g., {'prompt_tokens': 10, 'completion_tokens': 20}
        
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        tokens = prompt_tokens + completion_tokens

        # FIX: Calculate execution time using datetime objects if available.
        execution_time = 0.0
        if msg.sent_time and msg.recv_time:
             # Ensure sent_time and recv_time are datetime objects
            if isinstance(msg.sent_time, (int, float)) and isinstance(msg.recv_time, (int, float)):
                execution_time = msg.sent_time - msg.recv_time
            elif isinstance(msg.sent_time, datetime.datetime) and isinstance(msg.recv_time, datetime.datetime):
                execution_time = (msg.sent_time - msg.recv_time).total_seconds()


        try:
            action_name = msg.cause_by.__name__ if hasattr(msg.cause_by, '__name__') else str(msg.cause_by)
        except (AttributeError, IndexError):
            action_name = "UnknownAction"

        # Update action-specific stats
        stats = self._action_stats[action_name]
        stats['calls'] += 1
        stats['total_execution_time_seconds'] += execution_time

        if tokens > 0 or cost > 0:
            stats['total_tokens'] += tokens
            stats['total_cost_usd'] += cost
            
            # Update overall LLM stats
            self._overall_stats['total_llm_tokens'] += tokens
            self._overall_stats['total_llm_cost_usd'] += cost

        # Update overall execution time
        self._overall_stats['total_execution_time_seconds'] += execution_time

    def get_performance_report(self) -> dict:
        report = {
            'overall': self._overall_stats.copy(),
            'by_action': {}
        }

        for action, stats in self._action_stats.items():
            report['by_action'][action] = {
                'calls': stats['calls'],
                'total_tokens': stats['total_tokens'],
                'total_cost_usd': stats['total_cost_usd'],
                'total_execution_time_seconds': stats['total_execution_time_seconds'],
                'average_tokens_per_call': stats['total_tokens'] / stats['calls'] if stats['calls'] > 0 else 0,
                'average_cost_per_call_usd': stats['total_cost_usd'] / stats['calls'] if stats['calls'] > 0 else 0,
                'average_execution_time_seconds': stats['total_execution_time_seconds'] / stats['calls'] if stats['calls'] > 0 else 0
            }
        return report