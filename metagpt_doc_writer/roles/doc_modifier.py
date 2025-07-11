# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/doc_modifier.py (已修复)

import re
from metagpt.schema import Message
from metagpt_doc_writer.roles.base_role import MyBaseRole
from metagpt_doc_writer.schemas.doc_structures import (
    ValidatedChangeSet,
    FullDraft,
    Change,
)
from metagpt.logs import logger

class DocModifier(MyBaseRole):
    name: str = "DocModifier"
    profile: str = "Document Modifier"
    goal: str = "Apply validated changes to documents accurately"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])  # This is a non-LLM, deterministic role
        self._watch({ValidatedChangeSet})  # Watches for validated change sets

    async def _act(self) -> Message:
        """
        Applies a validated changeset to the latest full draft in memory.
        """
        logger.info(f"Executing action: {self.name}")
        
        # 1. Get the latest changeset and draft from memory
        memories = self.get_memories()
        try:
            # FIX: Iterate through memory to find the latest message of the correct type
            changeset_msg = next(m for m in reversed(memories) if isinstance(m.instruct_content, ValidatedChangeSet))
            full_draft_msg = next(m for m in reversed(memories) if isinstance(m.instruct_content, FullDraft))
        except StopIteration:
            logger.warning("No ValidatedChangeSet or FullDraft found in memory. Nothing to do.")
            return None

        current_content = full_draft_msg.instruct_content.content
        changes = changeset_msg.instruct_content.changes

        # 2. Apply changes
        logger.info(f"Applying {len(changes)} changes to the draft.")
        new_content = self._apply_changes(current_content, changes)

        # 3. Create a new FullDraft message
        new_draft = FullDraft(content=new_content, version=full_draft_msg.instruct_content.version + 1)
        
        return Message(content=f"Document modified with {len(changes)} changes.", instruct_content=new_draft)

    def _apply_changes(self, content: str, changes: list[Change]) -> str:
        """
        Applies a list of changes to the document content based on anchor IDs.
        """
        for change in changes:
            if not hasattr(change, 'anchor_id') or not change.anchor_id:
                logger.warning(f"Skipping change due to missing anchor_id: {change.comment}")
                continue

            start_pattern = re.escape(f"[anchor-id::{change.anchor_id}]")
            # FIX: Use \\Z to avoid DeprecationWarning
            regex_pattern = f"({start_pattern})(.*?)(?=\\[anchor-id::|\\Z)"
            
            match = re.search(regex_pattern, content, flags=re.DOTALL | re.MULTILINE)
            if not match:
                logger.warning(f"Anchor '{change.anchor_id}' not found. Skipping change: {change.comment}")
                continue
            
            logger.info(f"Processing operation '{change.operation}' for anchor '{change.anchor_id}'")

            if change.operation == "REPLACE_BLOCK":
                replacement = f"\\1{change.new_content}"
                content = re.sub(regex_pattern, replacement, content, count=1, flags=re.DOTALL | re.MULTILINE)

            elif change.operation == "INSERT_AFTER":
                replacement = f"\\g<0>{change.new_content}"
                content = re.sub(regex_pattern, replacement, content, count=1, flags=re.DOTALL | re.MULTILINE)

            elif change.operation == "DELETE_SECTION":
                content = re.sub(regex_pattern, "", content, count=1, flags=re.DOTALL | re.MULTILINE)
            
            else:
                logger.warning(f"Unknown operation '{change.operation}'. Skipping.")

        return content