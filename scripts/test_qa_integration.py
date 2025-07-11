# 路径: /root/metagpt/mgfr/scripts/test_qa_integration.py (Monkeypatch修复版)

import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock
import pytest

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- 导入所有需要的角色和组件 ---
from metagpt.schema import Message
from metagpt.logs import logger
# 从具体模块导入
from metagpt_doc_writer.roles.doc_assembler import DocAssembler
from metagpt_doc_writer.roles.chief_pm import ChiefPM
from metagpt_doc_writer.roles.qa_agent import QAAgent
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft, QAReport, QAFeedback

@pytest.mark.asyncio
async def test_qa_integration_flow(monkeypatch): # FIX: 引入 monkeypatch fixture
    """
    Tests the integration of QAAgent into the review loop using a stable mock.
    Flow: DocAssembler -> QAAgent -> ChiefPM
    """
    logger.info("--- 启动 QA 整合流程测试 ---")

    # --- 0. 准备一个全局的 Mock LLM ---
    mock_llm = AsyncMock()
    # 使用 monkeypatch 来替换框架底层的LLM创建函数
    from metagpt import context
    monkeypatch.setattr(context, "create_llm_instance", lambda _: mock_llm)

    # --- 1. 初始内容和草稿 ---
    sections = [DraftSection(chapter_id="1", content="## Chapter 1\n\nThis intro is short.")]
    assembler = DocAssembler()
    for sec in sections:
        assembler.rc.memory.add(Message(instruct_content=sec))
    assembled_msg = await assembler._act()
    current_draft = assembled_msg.instruct_content
    logger.info(f"\n[V{current_draft.version}] Assembled Draft created.")
    assert current_draft is not None

    # --- 2. QA Agent 执行质检 ---
    qa_agent = QAAgent() # QAAgent在初始化时会自动获得被monkeypatch的mock_llm
    
    # 定义Mock LLM对QA Agent的返回值
    mock_qa_report_data = { "feedbacks": [{"feedback_type": "Clarity", "description": "Intro is too short.", "suggestion": "Expand it."}] }
    mock_llm.aask = AsyncMock(return_value=json.dumps(mock_qa_report_data))
    
    qa_agent.rc.memory.add(assembled_msg)
    qa_report_msg = await qa_agent._act()
    logger.info("\n[QA] QAAgent generated a report.")
    assert isinstance(qa_report_msg.instruct_content, QAReport)
    # FIX: 断言现在应该能稳定通过，因为mock是可靠的
    assert len(qa_report_msg.instruct_content.feedbacks) == 1
    assert qa_report_msg.instruct_content.feedbacks[0].feedback_type == "Clarity"


    # --- 3. ChiefPM 结合QA报告进行审阅 ---
    chief_pm = ChiefPM() # ChiefPM同样会自动获得mock_llm
    
    # 为ChiefPM的调用设置一个新的返回值
    mock_llm.aask = AsyncMock(return_value="Feedback based on QA report.")
    
    chief_pm.rc.memory.add(assembled_msg)
    chief_pm.rc.memory.add(qa_report_msg)
    await chief_pm._act()

    # --- 4. **关键验证** ---
    mock_llm.aask.assert_called_once()
    final_prompt = mock_llm.aask.call_args[0][0]
    
    logger.info(f"\n[Verification] Prompt passed to ChiefPM's LLM:\n---PROMPT START---\n{final_prompt}\n---PROMPT END---")
    
    assert "QA REPORT" in final_prompt
    assert "Intro is too short." in final_prompt
    assert "Expand it." in final_prompt
    
    logger.info("\n--- QA 整合流程测试成功！ ---")