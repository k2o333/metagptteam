import json
import pytest
from hierarchical.actions.research_model import ToolExecutionResult, ToolExecutionStatus

def test_tool_execution_result_is_json_serializable():
    """
    验证 ToolExecutionResult.to_dict() 的输出可以被成功序列化。
    这是一个契约测试。
    """
    result = ToolExecutionResult(
        status=ToolExecutionStatus.SUCCESS,
        source="test_source",
        raw_data={"key": "value"},
        reason="A test reason"
    )
    
    try:
        # 核心断言：必须能无错地 dump 成 JSON
        json_str = json.dumps(result.to_dict())
        # 可选：验证反序列化后的值
        data = json.loads(json_str)
        assert data['status'] == 'success'
    except TypeError:
        pytest.fail("ToolExecutionResult.to_dict() is not JSON serializable!")