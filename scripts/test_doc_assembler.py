# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/doc_assembler.py

import hashlib
from .base_role import MyBaseRole
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft
from metagpt.logs import logger
import re

class DocAssembler(MyBaseRole):
    name: str = "DocAssembler"
    profile: str = "Document Assembler"
    goal: str = "Assemble draft sections into a full document with stable anchors"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])  # Non-LLM, deterministic role
        # Watches for a list of draft sections to trigger assembly
        self._watch({DraftSection}) 

    async def _act(self) -> Message:
        """
        Assembles a FullDraft from all DraftSection messages in memory.
        """
        logger.info(f"Executing action: {self.name}")
        
        # Correctly filter DraftSection messages from memory
        draft_sections = [msg.instruct_content for msg in self.get_memories() if isinstance(msg.instruct_content, DraftSection)]
        
        if not draft_sections:
            logger.warning("No DraftSection found in memory. Nothing to assemble.")
            return None

        logger.info(f"Assembling {len(draft_sections)} draft sections.")
        full_content_with_anchors = self._assemble_with_hashed_anchors(draft_sections)
        
        new_draft = FullDraft(content=full_content_with_anchors, version=1)
        
        logger.info("Document assembled successfully with hashed anchors.")
        return Message(content="Full document assembled.", instruct_content=new_draft)

    def _assemble_with_hashed_anchors(self, sections: list[DraftSection]) -> str:
        """
        Assembles sections into a single document, adding a stable, content-based
        hashed anchor ID to each significant paragraph or block.
        """
        # Sort sections based on chapter_id to ensure correct order
        sorted_sections = sorted(sections, key=lambda s: s.chapter_id)
        
        full_content_parts = []
        for section in sorted_sections:
            # Split section content into paragraphs (handling multiple newlines)
            paragraphs = re.split(r'\n\s*\n', section.content.strip())
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Create a stable hash from the paragraph content
                # We use the first 256 chars to balance uniqueness and performance
                anchor_text = para[:256]
                anchor_id = hashlib.sha1(anchor_text.encode()).hexdigest()[:12]
                
                # Prepend the anchor to the paragraph
                full_content_parts.append(f"[anchor-id::{anchor_id}]\n{para}")
                
        return "\n\n".join(full_content_parts)

    def _finalize_document(self, draft: FullDraft) -> str:
        """
        Removes all anchor IDs from the document for final delivery.
        """
        logger.info("Finalizing document by removing all anchor IDs.")
        # Regex to find and remove the anchor tags
        final_content = re.sub(r'\[anchor-id::[a-f0-9]{12}\]\n', '', draft.content)
        return final_content