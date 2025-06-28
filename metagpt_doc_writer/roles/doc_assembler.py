
import uuid
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft

class DocAssembler(Role):
    def __init__(self, name="DocAssembler", profile="Document Assembler", goal="Assemble and finalize documents", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([]) # Non-LLM role
        self._watch({DraftSection, FullDraft}) # Watches for draft sections and finalization requests

    async def _act(self) -> Message:
        # This role is deterministic and driven by messages, so we'll implement logic based on message type.
        # The actual logic will be in helper methods.
        # For now, this is a placeholder.
        # In a real scenario, you'd check the message type and call the appropriate method.
        print("DocAssembler is acting...")
        return None # Placeholder

    def _assemble_with_anchors(self, sections: list[DraftSection]) -> str:
        """Assembles sections into a single document with unique anchor IDs."""
        sorted_sections = sorted(sections, key=lambda s: s.chapter_id)
        full_content = []
        for section in sorted_sections:
            anchor_id = f"[anchor-id::{uuid.uuid4()}]"
            full_content.append(f"{anchor_id}{section.content}")
        return "\n\n".join(full_content)

    def _finalize_document(self, draft: FullDraft) -> str:
        """Removes all anchor IDs from the document."""
        import re
        final_content = re.sub(r'\[anchor-id::.*?\]', '', draft.content)
        return final_content
