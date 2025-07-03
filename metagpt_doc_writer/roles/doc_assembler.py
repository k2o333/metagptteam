
from metagpt.logs import logger
import uuid
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft
from pathlib import Path

class DocAssembler(Role):
    name: str = "DocAssembler"
    profile: str = "Document Assembler"
    goal: str = "Assemble and finalize documents"

    def __init__(self, output_path: str = "./data/outputs", **kwargs):
        super().__init__(**kwargs)
        self.set_actions([]) # Non-LLM role
        self._watch({DraftSection, FullDraft}) # Watches for draft sections and finalization requests
        self.output_path = Path(output_path)

    async def _act(self) -> Message:
        logger.info(f"DocAssembler _act called. News count: {len(self.rc.news)}")
        if not self.rc.news:
            return None

        messages = self.rc.news
        logger.debug(f"DocAssembler received messages: {[msg.dict() for msg in messages]}")
        
        # Check if we need to assemble a document
        draft_sections = [msg.instruct_content for msg in messages if isinstance(msg.instruct_content, DraftSection)]
        if draft_sections:
            logger.info(f"DocAssembler assembling {len(draft_sections)} draft sections.")
            full_content_with_anchors = self._assemble_with_anchors(draft_sections)
            new_draft = FullDraft(content=full_content_with_anchors)
            logger.info("DocAssembler assembled document with anchors.")
            return Message(content="Assembled document with anchors.", instruct_content=new_draft)

        # Check if we need to finalize a document (e.g., on an Approval message)
        finalize_requests = [msg.instruct_content for msg in messages if isinstance(msg.instruct_content, FullDraft)]
        if finalize_requests:
            logger.info(f"DocAssembler finalizing document. Received {len(finalize_requests)} FullDrafts.")
            final_content = self._finalize_document(finalize_requests[0])
            # Save the finalized document to disk
            self.output_path.mkdir(parents=True, exist_ok=True)
            output_file = self.output_path / "final_document.md"
            output_file.write_text(final_content)
            logger.info(f"Final document saved to {output_file}")
            return Message(content=f"Final document saved to {output_file}", instruct_content=None) 

        logger.info("DocAssembler found no relevant messages to act on.")
        return None

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
