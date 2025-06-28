
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, FullDraft, Change

class DocModifier(Role):
    def __init__(self, name="DocModifier", profile="Document Modifier", goal="Apply changes to documents", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([]) # Non-LLM role
        self._watch({ValidatedChangeSet}) # Watches for validated change sets

    async def _act(self) -> Message:
        # In a real scenario, this would be triggered by a message.
        # We would get the changeset and draft from memory.
        print("DocModifier is acting...")
        return None # Placeholder

    def _apply_changes(self, content: str, changes: list[Change]) -> str:
        """Applies a list of changes to the document content."""
        for change in changes:
            if change.operation == "REPLACE_BLOCK":
                # A more robust implementation would handle cases where the anchor is not found
                # For now, we assume valid changes
                anchor_start = f"[anchor-id::{change.anchor_id}]"
                # This is a simplified replacement. A real implementation would need to find the end of the block.
                # For now, we'll just replace the anchor itself with the new content.
                # This is a placeholder for a more complex implementation.
                content = content.replace(anchor_start, f"[anchor-id::{change.anchor_id}]{change.new_content}")
            elif change.operation == "INSERT_AFTER":
                anchor_start = f"[anchor-id::{change.anchor_id}]"
                # This is a simplified insertion. A real implementation would need to find the end of the block.
                content = content.replace(anchor_start, f"{anchor_start}{change.new_content}")
            # Add other operations like DELETE_SECTION here
        return content
