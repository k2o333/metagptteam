
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, FullDraft, Change
import re

class DocModifier(Role):
    name: str = "DocModifier"
    profile: str = "Document Modifier"
    goal: str = "Apply changes to documents"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([]) # Non-LLM role
        self._watch({ValidatedChangeSet}) # Watches for validated change sets

    async def _act(self) -> Message:
        # Get the latest ValidatedChangeSet and FullDraft from memory
        # Assuming the latest ValidatedChangeSet is the one to act upon
        changeset_msg = self.rc.memory.get_by_class(ValidatedChangeSet)[-1]
        # Assuming FullDraft is also in memory, perhaps from DocAssembler
        full_draft_msg = self.rc.memory.get_by_class(FullDraft)[-1]

        current_content = full_draft_msg.content
        changes = changeset_msg.instruct_content.changes

        new_content = self._apply_changes(current_content, changes)

        # Create a new FullDraft object with incremented version (if applicable)
        # For simplicity, we'll just create a new FullDraft for now.
        new_draft = FullDraft(content=new_content)

        return Message(content="Document modified.", instruct_content=new_draft)

    def _apply_changes(self, content: str, changes: list[Change]) -> str:
        """Applies a list of changes to the document content."""
        for change in changes:
            if change.operation == "REPLACE_BLOCK":
                # Find the block associated with the anchor_id and replace its content
                # This requires a more sophisticated parsing of the document to identify blocks.
                # For now, a simplified approach: replace the anchor and assume the content follows.
                # A robust solution would involve parsing the document into an AST or similar structure.
                anchor_pattern = re.escape(f"[anchor-id::{change.anchor_id}]")
                # This regex attempts to match the anchor and then capture everything until the next anchor or end of string.
                # This is still a simplification and might not work for all document structures.
                # A better approach would be to parse the document into blocks first.
                content = re.sub(f"({anchor_pattern})(.*?)(?=\[anchor-id::|$)", f"\\1{change.new_content}", content, flags=re.DOTALL)

            elif change.operation == "INSERT_AFTER":
                anchor_pattern = re.escape(f"[anchor-id::{change.anchor_id}]")
                content = re.sub(f"({anchor_pattern})", f"\\1{change.new_content}", content)
            
            elif change.operation == "DELETE_SECTION":
                # This is a placeholder. Deleting a section requires finding start and end anchors.
                # For now, we'll just remove the content between the anchors.
                if change.anchor_id and change.anchor_id_end:
                    start_pattern = re.escape(f"[anchor-id::{change.anchor_id}]")
                    end_pattern = re.escape(f"[anchor-id::{change.anchor_id_end}]")
                    # This regex attempts to match from start anchor to end anchor, including content.
                    content = re.sub(f"({start_pattern}).*?({end_pattern})", "", content, flags=re.DOTALL)
                elif change.anchor_id:
                    # If only anchor_id is provided for DELETE_SECTION, delete the block associated with it.
                    anchor_pattern = re.escape(f"[anchor-id::{change.anchor_id}]")
                    content = re.sub(f"({anchor_pattern})(.*?)(?=\[anchor-id::|$)", "", content, flags=re.DOTALL)

        return content
