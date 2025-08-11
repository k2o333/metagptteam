import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
# 修改导入路径，使用相对导入
from hierarchical.actions.tool_utils import (
    MCPToolSchemaDiscoverer, 
    ParameterGapAnalyzer, 
    ParameterCompletionExecutor
)
from hierarchical.actions.research_model import ToolExecutionStatus

# Test for MCPToolSchemaDiscoverer
class TestMCPToolSchemaDiscoverer:
    def test_get_schema_for_tool_found(self):
        # 创建模拟的 MCPManager 和 client
        mock_client = Mock()
        mock_client.tools = [
            {
                "name": "test-tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "A string parameter"},
                        "param2": {"type": "integer", "description": "An integer parameter"}
                    },
                    "required": ["param1"]
                }
            }
        ]
        
        mock_mcp_manager = Mock()
        mock_mcp_manager.tool_to_client_map = {"test-tool": mock_client}
        
        # 创建 discoverer 实例
        discoverer = MCPToolSchemaDiscoverer(mock_mcp_manager)
        
        # 调用方法
        schema = discoverer.get_schema_for_tool("test-tool")
        
        # 验证结果
        assert schema is not None
        assert schema["properties"]["param1"]["type"] == "string"
        assert schema["properties"]["param2"]["type"] == "integer"
        assert "param1" in schema["required"]
    
    def test_get_schema_for_tool_not_found(self):
        # 创建模拟的 MCPManager
        mock_mcp_manager = Mock()
        mock_mcp_manager.tool_to_client_map = {}
        
        # 创建 discoverer 实例
        discoverer = MCPToolSchemaDiscoverer(mock_mcp_manager)
        
        # 调用方法
        schema = discoverer.get_schema_for_tool("non-existent-tool")
        
        # 验证结果
        assert schema is None

# Test for ParameterGapAnalyzer
class TestParameterGapAnalyzer:
    def test_analyze_with_missing_required_params(self):
        # 创建 analyzer 实例
        analyzer = ParameterGapAnalyzer()
        
        # 定义 schema 和当前参数
        schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "A required string parameter"},
                "param2": {"type": "integer", "description": "An optional integer parameter"},
                "param3": {"type": "boolean", "description": "A required boolean parameter"}
            },
            "required": ["param1", "param3"]
        }
        
        current_args = {
            "param2": 42
        }
        
        # 调用方法
        missing_params = analyzer.analyze(schema, current_args)
        
        # 验证结果
        assert len(missing_params) == 2
        missing_param_names = [p["name"] for p in missing_params]
        assert "param1" in missing_param_names
        assert "param3" in missing_param_names
        
        # 验证参数详情
        param1_info = next(p for p in missing_params if p["name"] == "param1")
        assert param1_info["type"] == "string"
        assert param1_info["description"] == "A required string parameter"
        
        param3_info = next(p for p in missing_params if p["name"] == "param3")
        assert param3_info["type"] == "boolean"
        assert param3_info["description"] == "A required boolean parameter"
    
    def test_analyze_with_all_required_params_present(self):
        # 创建 analyzer 实例
        analyzer = ParameterGapAnalyzer()
        
        # 定义 schema 和当前参数
        schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "A required string parameter"},
                "param2": {"type": "integer", "description": "An optional integer parameter"}
            },
            "required": ["param1"]
        }
        
        current_args = {
            "param1": "test_value",
            "param2": 42
        }
        
        # 调用方法
        missing_params = analyzer.analyze(schema, current_args)
        
        # 验证结果
        assert len(missing_params) == 0

# Test for ParameterCompletionExecutor
class TestParameterCompletionExecutor:
    @pytest.mark.asyncio
    async def test_complete_parameters(self):
        # 创建模拟的 LLM
        mock_llm = AsyncMock()
        mock_llm.aask.return_value = '{"param1": "completed_value", "param3": true}'
        
        # 创建 executor 实例
        executor = ParameterCompletionExecutor(mock_llm)
        
        # 定义测试参数
        query_context = "Test query context"
        tool_name = "test-tool"
        existing_args = {"param2": 42}
        missing_params_info = [
            {"name": "param1", "type": "string", "description": "A required string parameter", "enum": None},
            {"name": "param3", "type": "boolean", "description": "A required boolean parameter", "enum": None}
        ]
        
        # 调用方法
        completed_params = await executor.complete_parameters(
            query_context, tool_name, existing_args, missing_params_info
        )
        
        # 验证结果
        assert "param1" in completed_params
        assert "param3" in completed_params
        assert completed_params["param1"] == "completed_value"
        assert completed_params["param3"] is True
        
        # 验证 LLM 被调用
        mock_llm.aask.assert_called_once()
    
    def test_parse_completion_result_with_json_code_block(self):
        # 创建 executor 实例
        executor = ParameterCompletionExecutor(None)
        
        # 定义包含 JSON 代码块的响应
        llm_response = '''
        Here is the completion result:
        ```json
        {
            "param1": "value1",
            "param2": 123
        }
        ```
        '''
        
        # 调用方法
        result = executor._parse_completion_result(llm_response)
        
        # 验证结果
        assert result["param1"] == "value1"
        assert result["param2"] == 123
    
    def test_parse_completion_result_with_plain_json(self):
        # 创建 executor 实例
        executor = ParameterCompletionExecutor(None)
        
        # 定义纯 JSON 响应
        llm_response = '{"param1": "value1", "param2": 123}'
        
        # 调用方法
        result = executor._parse_completion_result(llm_response)
        
        # 验证结果
        assert result["param1"] == "value1"
        assert result["param2"] == 123