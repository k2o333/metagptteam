# 路径: /root/metagpt/mgfr/scripts/test_full_revision_loop.py (最终修复版 V4)

import asyncio
import sys
import json
import hashlib
import re
from pathlib import Path
from unittest.mock import AsyncMock
import pytest

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- 导入真实的 metagpt 依赖 ---
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from pydantic import BaseModel
from typing import List, ClassVar

# =================================================================================
#  Schema 定义
# =================================================================================

class DraftSection(BaseModel):
    chapter_id: str
    content: str

class FullDraft(BaseModel):
    content: str
    version: int = 1

class ReviewNotes(BaseModel):
    feedback: str

class Change(BaseModel):
    operation: str
    anchor_id: str
    new_content: str = ""
    comment: str

class ValidatedChangeSet(BaseModel):
    changes: List[Change]

# =================================================================================
#  具体的 Action 和 Role 定义
# =================================================================================

class ReviewAndCommand(Action):
    async def run(self, messages: list[Message]) -> ReviewNotes:
        draft_msg = next((m for m in reversed(messages) if isinstance(m.instruct_content, FullDraft)), None)
        if not draft_msg: raise ValueError("No FullDraft found")
        prompt = "Review: {draft_content}"
        feedback_text = await self._aask(prompt.format(draft_content=draft_msg.instruct_content.content))
        return ReviewNotes(feedback=feedback_text)

class GenerateChangeSet(Action):
    # *** 关键修复点 1: 简化 run 方法的解析逻辑 ***
    async def run(self, messages: list[Message]) -> ValidatedChangeSet:
        notes_msg = next((m for m in reversed(messages) if isinstance(m.instruct_content, ReviewNotes)), None)
        draft_msg = next((m for m in reversed(messages) if isinstance(m.instruct_content, FullDraft)), None)
        if not (notes_msg and draft_msg): raise ValueError("Missing context")
        
        prompt = "Convert: {review_notes} for {draft_content}"
        response_json_str = await self._aask(prompt.format(review_notes=notes_msg.instruct_content.feedback, draft_content=draft_msg.instruct_content.content))
        
        try:
            # 对于测试，我们知道输入是纯JSON字符串，直接解析它。
            # 这也使得代码对纯净的LLM输出更具鲁棒性。
            data_dict = json.loads(response_json_str)
            return ValidatedChangeSet(**data_dict)
        except (json.JSONDecodeError, TypeError) as e:
            # 如果直接解析失败，再尝试使用 OutputParser 作为备用方案
            logger.warning(f"Direct JSON parsing failed: {e}. Falling back to OutputParser.")
            try:
                data_dict = OutputParser.parse_code(text=response_json_str)
                if isinstance(data_dict, str): data_dict = json.loads(data_dict)
                return ValidatedChangeSet(**data_dict)
            except Exception as ex:
                logger.error(f"Failed to parse ChangeSet with all methods: {ex}, output: {response_json_str}")
                return ValidatedChangeSet(changes=[])

# --- 自定义角色 ---
class DocAssembler(Role):
    def __init__(self, **kwargs): super().__init__(**kwargs); self.set_actions([])
    async def _act(self) -> Message:
        memories = self.get_memories()
        sections = [msg.instruct_content for msg in memories if isinstance(msg.instruct_content, DraftSection)]
        if not sections: return None
        sorted_sections = sorted(sections, key=lambda s: str(s.chapter_id))
        parts = []
        for sec in sorted_sections:
            paragraphs = re.split(r'\n\s*\n', sec.content.strip())
            for para in paragraphs:
                para = para.strip()
                if not para: continue
                anchor_id = hashlib.sha1(para.encode('utf-8')).hexdigest()[:12]
                parts.append(f"[anchor-id::{anchor_id}]\n{para}")
        content = "\n\n".join(parts)
        draft = FullDraft(content=content, version=1)
        return Message(content="Assembled", instruct_content=draft, cause_by=self.__class__)

class ChiefPM(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ReviewAndCommand])
        self._watch([DocAssembler])
    
    async def _act(self) -> Message:
        todo = self.rc.todo
        if todo is None: return None
        response_obj = await todo.run(self.rc.history)
        return Message(content=response_obj.model_dump_json(), instruct_content=response_obj, role=self.profile, cause_by=type(todo))

class ChangeSetGenerator(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateChangeSet])
        self._watch([ReviewAndCommand])
    
    async def _act(self) -> Message:
        todo = self.rc.todo
        if todo is None: return None
        response_obj = await todo.run(self.rc.history)
        return Message(content=response_obj.model_dump_json(), instruct_content=response_obj, role=self.profile, cause_by=type(todo))

class DocModifier(Role):
    def __init__(self, **kwargs): super().__init__(**kwargs); self.set_actions([])
    async def _act(self) -> Message:
        memories = self.get_memories()
        changeset_msg = next((m for m in reversed(memories) if isinstance(m.instruct_content, ValidatedChangeSet)), None)
        draft_msg = next((m for m in reversed(memories) if isinstance(m.instruct_content, FullDraft)), None)
        if not (changeset_msg and draft_msg) or not changeset_msg.instruct_content.changes: return None
        content = draft_msg.instruct_content.content
        version = draft_msg.instruct_content.version
        changes = changeset_msg.instruct_content.changes
        for change in changes:
            if not change.anchor_id: continue
            pattern = re.escape(f"[anchor-id::{change.anchor_id}]")
            regex = f"({pattern}.*?)(?=\\n\\[anchor-id::|\\Z)"
            if change.operation == "REPLACE_BLOCK":
                replacement_text = f"[anchor-id::{change.anchor_id}]\n{change.new_content}"
                content, count = re.subn(regex, replacement_text, content, 1, flags=re.DOTALL)
                if count == 0: logger.warning(f"Anchor '{change.anchor_id}' not found.")
        new_draft = FullDraft(content=content, version=version + 1)
        return Message(content="Modified", instruct_content=new_draft, cause_by=self.__class__)

# =================================================================================
#  测试函数
# =================================================================================

@pytest.mark.asyncio
async def test_full_automated_revision_loop_all_in_one(monkeypatch):
    logger.info("--- 启动 All-in-One 修订循环测试 ---")
    
    mock_llm = AsyncMock()
    pm_review_feedback = "The introduction is old..."
    anchor_id_to_replace = hashlib.sha1("Old introduction.".encode('utf-8')).hexdigest()[:12]
    new_content_str = "New and improved introduction."
    changeset_json = json.dumps({
        "changes": [{"operation": "REPLACE_BLOCK", "anchor_id": anchor_id_to_replace, "new_content": new_content_str, "comment": "Update intro"}]
    })
    mock_llm.aask.side_effect = [pm_review_feedback, changeset_json]

    from metagpt import context
    monkeypatch.setattr(context, "create_llm_instance", lambda _: mock_llm)
    
    # --- 步骤 1: 组装 ---
    assembler = DocAssembler()
    for msg in [Message(instruct_content=DraftSection(chapter_id="1", content="## Chapter 1\n\nOld introduction.")),
                Message(instruct_content=DraftSection(chapter_id="2", content="## Chapter 2\n\nContent to be kept."))]:
        assembler.rc.memory.add(msg)
    
    assembled_msg = await assembler._act()
    assert assembled_msg is not None, "Assembler did not produce a message"
    current_draft = assembled_msg.instruct_content
    logger.info(f"\n[V{current_draft.version}] Assembled Draft:\n{current_draft.content}")
    assert "[anchor-id::" in current_draft.content

    # --- 步骤 2: 审阅 ---
    chief_pm = ChiefPM()
    review_notes_msg = await chief_pm.run(assembled_msg)
    assert review_notes_msg is not None, "ChiefPM did not produce a message"
    logger.info(f"\n[Review] ChiefPM Feedback: '{review_notes_msg.instruct_content.feedback}'")
    assert mock_llm.aask.call_count == 1

    # --- 步骤 3: 生成指令 ---
    generator = ChangeSetGenerator()
    generator.rc.memory.add(assembled_msg) 
    changeset_msg = await generator.run(review_notes_msg)
    assert changeset_msg is not None, "ChangeSetGenerator did not produce a message"
    logger.info(f"\n[Generation] ChangeSet: {changeset_msg.instruct_content.model_dump_json(indent=2)}")
    assert mock_llm.aask.call_count == 2
    assert len(changeset_msg.instruct_content.changes) > 0

    # --- 步骤 4: 应用修改 ---
    modifier = DocModifier()
    modifier.rc.memory.add(assembled_msg)
    modifier.rc.memory.add(changeset_msg)
    modified_msg = await modifier._act()
    
    assert modified_msg is not None, "Modifier did not produce a message"
    final_draft = modified_msg.instruct_content
    logger.info(f"\n[V{final_draft.version}] Final Draft:\n{final_draft.content}")

    # --- 步骤 5: 验证 ---
    assert final_draft.version == 2
    assert "New and improved introduction." in final_draft.content
    assert "Old introduction." not in final_draft.content
    
    logger.info("\n--- All-in-One 修订循环测试成功！ ---")