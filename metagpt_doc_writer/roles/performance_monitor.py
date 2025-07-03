
import time
import json
from collections import defaultdict
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

class PerformanceMonitor(Role):
    """
    A non-LLM role that silently monitors the performance of the system.
    It records token usage, costs, and execution times for all actions.
    """
    def __init__(self, name="PerformanceMonitor", profile="Performance Monitor", goal="Monitor system performance", **kwargs):
        super().__init__(name=name, profile=profile, goal=goal, **kwargs)
        self.set_actions([])  # This is a non-LLM, deterministic role
        self._watch({Message})  # Subscribe to all messages to capture metadata

        self.start_time = time.time()
        self.action_metrics = defaultdict(lambda: {'calls': 0, 'total_tokens': 0, 'total_cost': 0, 'total_time': 0})
        self.total_tokens = 0
        self.total_cost = 0

    async def _observe(self, msg: Message) -> Message:
        """Observes messages and records performance metrics from their metadata."""
        if msg.cause_by:
            action_name = msg.cause_by.split('.')[-1] # Get the simple action name
            metrics = self.action_metrics[action_name]
            
            # Aggregate metrics if they exist in the message's metadata
            if msg.model_extra and 'extra_data' in msg.model_extra:
                extra_data = msg.model_extra['extra_data']
                if 'token_cost' in extra_data:
                    metrics['calls'] += 1
                    metrics['total_tokens'] += extra_data['token_cost'].total_prompt_tokens + extra_data['token_cost'].total_completion_tokens
                    metrics['total_cost'] += extra_data['token_cost'].total_cost
                    self.total_tokens += extra_data['token_cost'].total_prompt_tokens + extra_data['token_cost'].total_completion_tokens
                    self.total_cost += extra_data['token_cost'].total_cost

                if 'execution_time' in extra_data:
                    metrics['total_time'] += extra_data['execution_time']

        return await super()._observe(msg)

    def get_performance_report(self) -> dict:
        """Generates a detailed performance report."""
        total_execution_time = sum(v['total_time'] for v in self.action_metrics.values())
        
        report = {
            "overall": {
                "total_execution_time_seconds": round(total_execution_time, 2),
                "total_llm_tokens": self.total_tokens,
                "total_llm_cost_usd": round(self.total_cost, 4),
            },
            "by_action": {k: {
                'calls': v['calls'],
                'total_tokens': v['total_tokens'],
                'total_cost_usd': round(v['total_cost'], 4),
                'average_tokens_per_call': v['total_tokens'] // v['calls'] if v['calls'] > 0 else 0,
                'average_cost_per_call_usd': round(v['total_cost'] / v['calls'], 4) if v['calls'] > 0 else 0,
            } for k, v in self.action_metrics.items()}
        }
        return report

    def save_report(self, path: str = "performance_report.json"):
        """Saves the performance report to a file."""
        report = self.get_performance_report()
        logger.info(f"Saving performance report to {path}")
        with open(path, 'w') as f:
            json.dump(report, f, indent=4)
