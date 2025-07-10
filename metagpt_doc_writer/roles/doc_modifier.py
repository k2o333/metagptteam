# /root/metagpt/mgfr/metagpt_doc_writer/roles/doc_modifier.py

from .base_role import MyBaseRole
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, FullDraft, Change
import re

class DocModifier(MyBaseRole):
    name: str = "DocModifier"
    profile: str = "Document Modifier"
    goal: str = "Apply changes to documents"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([]) # Non-LLM role
        self._watch({ValidatedChangeSet}) # Watches for validated change sets

    async def _act(self) -> Message:
        # Correctly filter messages from memory
        memories = self.get_memories()
        changeset_msg = [m for m in memories if isinstance(m.instruct_content, ValidatedChangeSet)][-1]
        full_draft_msg = [m for m in memories if isinstance(m.instruct_content, FullDraft)][-1]

        current_content = full_draft_msg.instruct_content.content
        changes = changeset_msg.instruct_content.changes

        new_content = self._apply_changes(current_content, changes)

        new_draft = FullDraft(content=new_content)

        return Message(content="Document modified.", instruct_content=new_draft)

    def _apply_changes(self, content: str, changes: list[Change]) -> str:
        """Applies a list of changes to the document content."""
        for change in changes:
            # Check for anchor_id and construct a regex pattern for the block.
            if not hasattr(change, 'anchor_id') or not change.anchor_id:
                continue # Skip changes without a valid anchor_id

            # A block is from one anchor_id to the next, or to the end of the file.
            # Use re.escape to handle special characters in the anchor_id itself.
            start_pattern = re.escape(change.anchor_id)
            # The regex looks for the start pattern, captures everything until the next anchor pattern or end of string.
            regex_pattern = f"(\\[anchor-id::{start_pattern}\\])(.*?)(?=\\[anchor-id::|\\Z)"
            
            if change.operation == "REPLACE_BLOCK":
                # Replace the content of the block (group 2) associated with anchor_id.
                # The replacement includes the anchor tag (group 1) and the new content.
                content = re.sub(regex_pattern, f"\\1{change.new_content}", content, flags=re.DOTALL | re.MULTILINE)

            elif change.operation == "INSERT_AFTER":
                # Insert new_content after the block associated with anchor_id.
                # The replacement includes the original block (group 0) and the new content.
                content = re.sub(regex_pattern, f"\\g<0>{change.new_content}", content, flags=re.DOTALL | re.MULTILINE)
            
            elif change.operation == "DELETE_SECTION":
                # Delete the block associated with anchor_id.
                content = re.sub(regex_pattern, "", content, flags=re.DOTALL | re.MULTILINE)

        return content