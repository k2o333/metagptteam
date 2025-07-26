# mghier/tests/test_chief_pm.py (最终修复版)

import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from metagpt.actions import UserRequirement
from metagpt.schema import Message

from hierarchical.actions import CreateSubOutline, Research
from hierarchical.roles import ChiefPM
from hierarchical.schemas import Outline
from hierarchical.context import HierarchicalContext

def create_mock_context():
    """创建一个带有必要mock属性的 HierarchicalContext Mock对象。"""
    mock_context = MagicMock(spec=HierarchicalContext)
    mock_context.config = MagicMock()
    mock_context.config.llm.api_type = "openai"
    mock_context.kwargs = {"custom_config": {}}
    mock_context.cost_manager = MagicMock()
    mock_llm = MagicMock()
    mock_context.llm_with_cost_manager_from_llm_config.return_value = mock_llm
    mock_context.outline = Outline(goal="test goal")
    return mock_context

@pytest.mark.asyncio
async def test_chief_pm_handles_research_success():
    """测试当研究成功时，ChiefPM能正确处理结果并传递给下一环节。"""
    # 准备
    mock_context = create_mock_context()
    chief_pm = ChiefPM(context=mock_context)
    
    # 【核心修复】直接向真实的memory对象中添加一条模拟消息
    mock_user_req_msg = Message(content="test requirement", cause_by=UserRequirement)
    chief_pm.rc.memory.add(mock_user_req_msg)

    # Mock _execute_action 方法
    mock_success_result = {
        "test goal": {
            "status": "success",
            "data": {"info": "This is a successful research result."}
        }
    }
    chief_pm._execute_action = AsyncMock(side_effect=[
        mock_success_result, 
        [] 
    ])

    # 执行
    await chief_pm._act()

    # 断言
    assert chief_pm._execute_action.call_count == 2
    
    # 验证对 Research Action 的调用
    research_call_args = chief_pm._execute_action.call_args_list[0]
    assert isinstance(research_call_args.args[0], Research)
    assert research_call_args.kwargs['queries'] == ["test goal"]

    # 验证对 CreateSubOutline Action 的调用
    create_outline_call_args = chief_pm._execute_action.call_args_list[1]
    assert isinstance(create_outline_call_args.args[0], CreateSubOutline)
    kwargs = create_outline_call_args.kwargs
    assert "research_context" in kwargs
    assert 'successful research result' in kwargs['research_context']
    assert kwargs['goal'] == "test goal"


@pytest.mark.asyncio
async def test_chief_pm_handles_research_failure():
    """测试当研究失败时，ChiefPM能优雅地继续。"""
    # 准备
    mock_context = create_mock_context()
    chief_pm = ChiefPM(context=mock_context)
    
    # 【核心修复】直接向真实的memory对象中添加一条模拟消息
    mock_user_req_msg = Message(content="test requirement", cause_by=UserRequirement)
    chief_pm.rc.memory.add(mock_user_req_msg)
    
    # 模拟 _execute_action
    mock_failure_result = {
        "test goal": { "status": "failure", "reason": "MCP tool timed out." }
    }
    chief_pm._execute_action = AsyncMock(side_effect=[
        mock_failure_result,
        []
    ])
    
    # 执行
    await chief_pm._act()
    
    # 断言
    assert chief_pm._execute_action.call_count == 2
    create_outline_call_args = chief_pm._execute_action.call_args_list[1]
    kwargs = create_outline_call_args.kwargs
    assert "research_context" in kwargs
    assert 'No specific research context' in kwargs['research_context']
    assert kwargs['goal'] == "test goal"