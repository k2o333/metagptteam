# tests/test_context7_adapter.py (最终修正版 - 解决日志捕获问题)
import sys
from pathlib import Path
import pytest
import requests
# import logging # 不再需要导入 logging，因为我们直接mock metagpt的logger

# 确保能找到 hierarchical 模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.rag.adapters.context7_adapter import Context7Adapter

@pytest.fixture
def adapter():
    """提供一个Context7Adapter的实例用于测试。"""
    return Context7Adapter(base_url="http://fake-context7.com", api_key="fake-key")

def test_query_success(mocker, adapter):
    """AC2.2: 测试成功的query调用，并断言payload和返回结果。"""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"status": "success", "data": ["result1"]}
    mock_response.raise_for_status.return_value = None
    
    mock_post = mocker.patch("requests.Session.post", return_value=mock_response)
    
    query_text = "test query"
    agent = "Writer"
    params = {"limit": 10}
    result = adapter.query(query_text, agent, params)
    
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["json"]["query"] == query_text
    assert mock_post.call_args.kwargs["json"]["agentType"] == agent
    assert mock_post.call_args.kwargs["json"]["params"]["limit"] == 10
    
    assert result["status"] == "success"
    assert result["data"] == ["result1"]

def test_query_request_exception_triggers_fallback(mocker, adapter): # 【修正】: 移除 caplog 参数
    """AC2.2: 测试当requests抛出异常时，能够调用fallback。"""
    # 【核心修正】: Mock MetaGPT的logger
    mock_logger = mocker.patch("hierarchical.rag.adapters.context7_adapter.logger") 

    mocker.patch(
        "requests.Session.post",
        side_effect=requests.exceptions.ConnectionError("Test connection error")
    )
    mocker.spy(adapter, "_fallback_search") 
    
    query_text = "another query"
    result = adapter.query(query_text, "Reviewer")
    
    assert result["status"] == "error"
    assert result["original_query"] == query_text
    assert "fallback mechanism activated" in result["message"]
    
    adapter._fallback_search.assert_called_once_with(query_text)
    
    # 断言 mock_logger 的 warning 方法被调用，并检查其参数
    mock_logger.warning.assert_called_once()
    # call_args 是一个元组: (args, kwargs)
    # args[0] 是第一个位置参数，即日志消息字符串
    warning_message = mock_logger.warning.call_args[0][0]
    assert "Context7 query failed" in warning_message
    assert "Test connection error" in warning_message

def test_audit_query_success(mocker, adapter):
    """测试成功的audit_query调用。"""
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mock_post = mocker.patch("requests.Session.post", return_value=mock_response)
    
    result = adapter.audit_query("audited query", "Archiver")
    
    assert result is True
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["json"]["agentType"] == "Archiver"