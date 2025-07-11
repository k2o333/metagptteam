# 路径: /root/metagpt/mgfr/scripts/test_qa_agent.py (断言修正版)

import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock
import pytest

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- 导入待测试模块和依赖 ---
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.roles.qa_agent import QAAgent
from metagpt_doc_writer.schemas.doc_structures import FullDraft, QAReport

@pytest.mark.asyncio
async def test_qa_agent_run():
    """
    Tests that the QAAgent can review a draft and produce a structured QAReport.
    """
    logger.info("--- 启动 QAAgent 单元测试 ---")

    # 1. 准备一份有明显问题的草稿
    draft_content = (
        "# Chapter 1\n\n"
        "This is a test. The term 'Big Model' is used here.\n\n"
        "## Section 1.1\n\n"
        "Later, we talk about 'Large Model'. This is an inconsistency.\n\n"
        "Also, this part is [TBD]."
    )
    test_draft = FullDraft(content=draft_content, version=1)

    # 2. 准备 Mock LLM 的返回值
    # FIX: 更新 mock 数据以匹配真实LLM可能返回的更精确的类型
    mock_qa_report_json = {
        "feedbacks": [
            {
                "feedback_type": "Terminology Consistency", # <- 使用更精确的类型
                "description": "The terms 'Big Model' and 'Large Model' are used interchangeably.",
                "suggestion": "Choose one term, e.g., 'Large Model', and use it consistently throughout the document."
            },
            {
                "feedback_type": "Completeness",
                "description": "Placeholder text '[TBD]' was found.",
                "suggestion": "Replace '[TBD]' with the actual content."
            }
        ]
    }

    # 3. 创建 QAAgent 并注入 Mock LLM
    qa_agent = QAAgent()
    mock_llm = AsyncMock()
    mock_llm.aask = AsyncMock(return_value=json.dumps(mock_qa_report_json))
    qa_agent.set_llm(mock_llm)

    # 4. 将草稿放入 QAAgent 的记忆中并执行
    qa_agent.rc.memory.add(Message(instruct_content=test_draft))
    
    # 5. 执行_act方法
    result_message = await qa_agent._act()

    # 6. 验证结果
    assert result_message is not None, "QAAgent should produce a message."
    
    qa_report = result_message.instruct_content
    assert isinstance(qa_report, QAReport), "The message content should be a QAReport."
    logger.info(f"Generated QA Report:\n{qa_report.model_dump_json(indent=2)}")
    
    assert len(qa_report.feedbacks) == 2
    # FIX: 更新断言以匹配新的期望值
    assert qa_report.feedbacks[0].feedback_type == "Terminology Consistency"
    assert qa_report.feedbacks[1].feedback_type == "Completeness"

    logger.info("--- QAAgent 单元测试通过！ ---")