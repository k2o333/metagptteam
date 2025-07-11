# 路径: /root/metagpt/mgfr/scripts/test_revision_loop.py (最终修复版)

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import hashlib  # FIX: 导入 hashlib 模块

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- 导入待测试模块和依赖 ---
from metagpt.schema import Message
from metagpt_doc_writer.roles.doc_assembler import DocAssembler
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft, ValidatedChangeSet, Change

# --- 模拟LLM环境的辅助函数 ---
def mock_role_env(role_instance: MagicMock):
    """Mocks the LLM dependency for a Role instance."""
    # This context manager patches the BaseLLM class for the duration of the 'with' block.
    # It's a clean way to handle mocking for object instantiation.
    with patch('metagpt.provider.base_llm.BaseLLM'):
        return role_instance

@pytest.mark.asyncio
async def test_assembly_and_modification_loop():
    """
    Tests the core loop: Assembling a doc, then modifying it.
    This validates that DocAssembler's hashed anchors are usable by DocModifier.
    """
    print("--- 启动文档组装与修订集成测试 ---")

    # --- 1. 准备阶段：定义原始章节 ---
    draft_sections = [
        DraftSection(chapter_id="chap1", content="## Chapter 1: The Beginning\n\nThis is the first paragraph."),
        DraftSection(chapter_id="chap2", content="## Chapter 2: The Middle\n\nThis is the second paragraph.\nIt has two lines."),
        DraftSection(chapter_id="chap3", content="## Chapter 3: The End\n\nThis is the final paragraph.")
    ]
    
    # --- 2. 组装阶段：调用 DocAssembler ---
    assembler = mock_role_env(DocAssembler())
    for section in draft_sections:
        assembler.rc.memory.add(Message(content="", instruct_content=section))

    print("\n--- Running DocAssembler ---")
    assembled_message = await assembler._act()
    assert assembled_message is not None, "Assembler should produce a message."
    
    initial_draft = assembled_message.instruct_content
    assert isinstance(initial_draft, FullDraft), "Assembled content should be a FullDraft."
    print("Initial Assembled Draft with Hashed Anchors:\n" + "="*40 + f"\n{initial_draft.content}")
    
    # 验证哈希锚点已生成
    assert "[anchor-id::" in initial_draft.content
    
    # --- 3. 修改阶段：手动定义修改指令并调用 DocModifier ---
    
    # 模拟一个修改指令：替换第二章的标题段落
    para_to_replace = "## Chapter 2: The Middle"
    anchor_to_replace_id = hashlib.sha1(para_to_replace.encode('utf-8')).hexdigest()[:12]
    
    changes_to_apply = [
        Change(
            operation="REPLACE_BLOCK", 
            anchor_id=anchor_to_replace_id, 
            new_content="## Chapter 2: The UPDATED Middle\n\nContent has been successfully modified.",
            comment="Update Chapter 2 title and content."
        )
    ]
    
    modifier = mock_role_env(DocModifier())
    # 将组装好的草稿和修改指令放入Modifier的记忆中
    modifier.rc.memory.add(assembled_message)
    modifier.rc.memory.add(Message(content="", instruct_content=ValidatedChangeSet(changes=changes_to_apply)))

    print(f"\n--- Running DocModifier to replace content at anchor '{anchor_to_replace_id}' ---")
    modified_message = await modifier._act()
    
    assert modified_message is not None, "Modifier should produce a message."
    
    modified_draft = modified_message.instruct_content
    assert isinstance(modified_draft, FullDraft), "Modified content should be a FullDraft."
    print("Final Modified Draft:\n" + "="*40 + f"\n{modified_draft.content}")

    # --- 4. 验证阶段：检查最终结果 ---
    assert "The UPDATED Middle" in modified_draft.content
    assert "The Middle" not in modified_draft.content
    assert initial_draft.content != modified_draft.content
    assert modified_draft.version == initial_draft.version + 1

    print("\n--- 文档组装与修订集成测试通过！ ---")