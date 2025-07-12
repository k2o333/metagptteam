# /root/metagpt/mgfr/metagpt_doc_writer/roles/doc_assembler.py (原生重构版)

import hashlib
import re
from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.actions.write_section import WriteSection # 用于监听
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft, ApprovedTask

class DocAssembler(DocWriterBaseRole):
    name: str = "DocAssembler"
    profile: str = "Document Assembler"
    goal: str = "Assemble draft sections into a full document with stable anchors"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([]) # 非LLM角色
        self._watch([WriteSection])
        self.total_tasks = 0

    async def _act(self) -> Message:
        # 在真实场景中，我们需要一个更好的方式来确定所有任务是否完成
        # 这里简化为：当收到一个DraftSection时，检查是否所有任务都完成了
        if self.total_tasks == 0:
            approved_tasks = [m for m in self.rc.memory.get() if isinstance(m.instruct_content, ApprovedTask)]
            self.total_tasks = len(approved_tasks)
            if self.total_tasks == 0: # 如果还没有ApprovedTask，则无法判断
                return None
        
        draft_sections = [m.instruct_content for m in self.rc.memory.get() if isinstance(m.instruct_content, DraftSection)]
        
        if len(draft_sections) < self.total_tasks:
            logger.info(f"{self.name} collected {len(draft_sections)}/{self.total_tasks} sections, waiting...")
            return None # 继续等待其他部分

        logger.info(f"Assembling {len(draft_sections)} draft sections.")
        full_content_with_anchors = self._assemble_with_hashed_anchors(draft_sections)
        
        last_version = 0
        try:
            last_draft_msg = next(m for m in reversed(self.rc.memory.get()) if isinstance(m.instruct_content, FullDraft))
            last_version = last_draft_msg.instruct_content.version
        except StopIteration:
            pass

        new_draft = FullDraft(content=full_content_with_anchors, version=last_version + 1)
        
        return Message(content=f"Full document assembled (Version {new_draft.version}).", instruct_content=new_draft, cause_by=self.__class__)

    def _assemble_with_hashed_anchors(self, sections: list[DraftSection]) -> str:
        sorted_sections = sorted(sections, key=lambda s: str(s.chapter_id))
        full_content_parts = []
        for section in sorted_sections:
            paragraphs = re.split(r'\n\s*\n', section.content.strip())
            for para in paragraphs:
                para = para.strip()
                if not para: continue
                anchor_text = para[:256]
                anchor_id = hashlib.sha1(anchor_text.encode('utf-8')).hexdigest()[:12]
                full_content_parts.append(f"[anchor-id::{anchor_id}]\n{para}")
        return "\n\n".join(full_content_parts)