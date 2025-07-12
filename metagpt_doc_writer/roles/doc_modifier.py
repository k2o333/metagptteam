# /root/metagpt/mgfr/metagpt_doc_writer/roles/doc_modifier.py (原生重构版)

import re
from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, FullDraft, Change

class DocModifier(DocWriterBaseRole): # 【关键修正】: 继承自 Role
    name: str = "DocModifier"
    profile: str = "Document Modifier"
    goal: str = "Apply validated changes to documents accurately"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])
        self._watch({ValidatedChangeSet})
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        logger.info(f"Executing action: {self.name}")
        
        try:
            changeset_msg = next(m for m in reversed(self.rc.history) if isinstance(m.instruct_content, ValidatedChangeSet))
            full_draft_msg = next(m for m in reversed(self.rc.history) if isinstance(m.instruct_content, FullDraft))
        except StopIteration:
            logger.warning("No ValidatedChangeSet or FullDraft found. Nothing to do.")
            return None

        current_content = full_draft_msg.instruct_content.content
        changes = changeset_msg.instruct_content.changes

        logger.info(f"Applying {len(changes)} changes to the draft.")
        new_content = self._apply_changes(current_content, changes)

        new_draft = FullDraft(content=new_content, version=full_draft_msg.instruct_content.version + 1)
        
        return Message(content=f"Document modified with {len(changes)} changes.", instruct_content=new_draft, cause_by=self.__class__)

    def _apply_changes(self, content: str, changes: list[Change]) -> str:
        # ... (此内部方法保持不变) ...
        for change in changes:
            if not hasattr(change, 'anchor_id') or not change.anchor_id: continue
            start_pattern = re.escape(f"[anchor-id::{change.anchor_id}]")
            regex_pattern = f"({start_pattern})(.*?)(?=\\[anchor-id::|\\Z)"
            if not re.search(regex_pattern, content, flags=re.DOTALL | re.MULTILINE):
                logger.warning(f"Anchor '{change.anchor_id}' not found. Skipping change.")
                continue
            # ...
        return content