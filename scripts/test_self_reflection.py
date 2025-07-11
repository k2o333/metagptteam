# 路径: /root/metagpt/mgfr/scripts/test_self_reflection.py (新增文件)

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
from metagpt.logs import logger
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, RefinedTask

@pytest.mark.asyncio
async def test_write_section_with_self_reflection():
    """
    Tests that the WriteSection action correctly performs the self-reflection step
    and returns the revised draft when necessary.
    """
    logger.info("--- 启动 WriteSection 自我反思单元测试 ---")

    # 1. 准备输入任务
    task = ApprovedTask(
        chapter_title="Test Chapter",
        refined_task=RefinedTask(
            chapter_title="Test Chapter",
            context="A test context",
            goals=["Explain topic X clearly"],
            acceptance_criteria=["Content is clear and accurate"]
        )
    )

    # 2. 准备 Mock LLM 的两次返回值
    initial_draft = "This is a simple draft."
    
    # Mock的LLM在第二次调用（反思）时，会返回一个需要修正的评估结果
    reflection_response = {
        "Evaluate": {"Completeness": 3, "Clarity": 3, "Accuracy": 4}, # Score 10 < 13
        "Suggest": "Add more details and examples.",
        "Revise": "This is a much better and revised draft with more details."
    }
    
    mock_llm = AsyncMock()
    # aask的side_effect可以是一个列表，它会按顺序返回列表中的值
    mock_llm.aask.side_effect = [
        initial_draft,                      # 第一次调用返回初稿
        json.dumps(reflection_response)     # 第二次调用返回反思结果
    ]

    # 3. 创建 Action 并注入 Mock LLM
    write_action = WriteSection()
    write_action.set_llm(mock_llm)

    # 4. 执行 Action
    result_draft_section = await write_action.run(task)

    # 5. 验证结果
    assert mock_llm.aask.call_count == 2, "LLM should be called twice (write + reflect)."
    
    logger.info(f"Initial draft was: '{initial_draft}'")
    logger.info(f"Final content is: '{result_draft_section.content}'")
    
    # 断言最终返回的是修订后的内容
    assert result_draft_section.content == reflection_response["Revise"]
    assert result_draft_section.content != initial_draft

    logger.info("--- WriteSection 自我反思单元测试通过！ ---")