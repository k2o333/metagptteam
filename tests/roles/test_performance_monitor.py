
import pytest
import asyncio
from metagpt.schema import Message
from metagpt.utils.cost_manager import Costs
from metagpt_doc_writer.roles.performance_monitor import PerformanceMonitor

@pytest.mark.asyncio
async def test_performance_monitor_aggregation():
    # Arrange
    monitor = PerformanceMonitor()
    
    # Act: Simulate observing messages with performance metadata
    msg1 = Message(
        content="Test message 1", 
        cause_by="metagpt_doc_writer.actions.some_action.SomeAction",
        extra_data={'token_cost': Costs(total_prompt_tokens=100, total_completion_tokens=200, total_cost=0.001, total_budget=0), 'execution_time': 0.5}
    )

    msg2 = Message(
        content="Test message 2", 
        cause_by="metagpt_doc_writer.actions.some_action.SomeAction",
        extra_data={'token_cost': Costs(total_prompt_tokens=50, total_completion_tokens=100, total_cost=0.0005, total_budget=0), 'execution_time': 0.3}
    )

    msg3 = Message(
        content="Test message 3", 
        cause_by="metagpt_doc_writer.actions.another_action.AnotherAction",
        extra_data={'token_cost': Costs(total_prompt_tokens=300, total_completion_tokens=600, total_cost=0.003, total_budget=0), 'execution_time': 1.2}
    )

    await monitor._observe(msg1)
    await monitor._observe(msg2)
    await monitor._observe(msg3)

    # Assert
    report = monitor.get_performance_report()

    # Overall stats
    assert report['overall']['total_llm_tokens'] == 100 + 200 + 50 + 100 + 300 + 600
    assert report['overall']['total_llm_cost_usd'] == pytest.approx(0.0045)
    assert report['overall']['total_execution_time_seconds'] > 0

    # Per-action stats
    some_action_stats = report['by_action']['SomeAction']
    assert some_action_stats['calls'] == 2
    assert some_action_stats['total_tokens'] == 450
    assert some_action_stats['total_cost_usd'] == pytest.approx(0.0015)
    assert some_action_stats['average_tokens_per_call'] == 225

    another_action_stats = report['by_action']['AnotherAction']
    assert another_action_stats['calls'] == 1
    assert another_action_stats['total_tokens'] == 900
    assert another_action_stats['total_cost_usd'] == pytest.approx(0.003)
