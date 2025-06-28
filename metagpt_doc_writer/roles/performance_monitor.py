
import time
from metagpt.roles import Role
from metagpt.schema import Message

class PerformanceMonitor(Role):
    def __init__(self, name="PerformanceMonitor", profile="Performance Monitor", goal="Monitor the performance of the system", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([]) # Non-LLM role
        self._watch({Message}) # Watches all messages
        self.start_time = time.time()
        self.message_count = 0

    async def _observe(self, msg: Message) -> Message:
        self.message_count += 1
        return msg

    def get_performance_report(self):
        end_time = time.time()
        return {
            "total_time_seconds": end_time - self.start_time,
            "total_messages": self.message_count
        }
