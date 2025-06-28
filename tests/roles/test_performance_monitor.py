
import asyncio
from metagpt.schema import Message
from metagpt_doc_writer.roles.performance_monitor import PerformanceMonitor

@pytest.mark.asyncio
async def test_performance_monitor():
    monitor = PerformanceMonitor()
    # Simulate observing messages
    await monitor._observe(Message(content="Message 1"))
    await monitor._observe(Message(content="Message 2"))

    report = monitor.get_performance_report()
    assert report["total_messages"] == 2
    assert report["total_time_seconds"] > 0
