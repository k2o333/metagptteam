# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/doc_assembler.py (已修复)

import hashlib
import re
from .base_role import MyBaseRole
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft
from metagpt.logs import logger

class DocAssembler(MyBaseRole):
    name: str = "DocAssembler"
    profile: str = "Document Assembler"
    goal: str = "Assemble draft sections into a full document with stable anchors"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])  # Non-LLM, deterministic role
        # It watches for DraftSection, but its _act is designed to be robust even if called directly.
        self._watch({DraftSection}) 

    async def _act(self) -> Message:
        """
        Assembles a FullDraft from all DraftSection messages in memory.
        This method is now robust and works by checking memory directly,
        not just news.
        """
        logger.info(f"Executing action: {self.name}")
        
        # FIX: Instead of relying on rc.news, directly get all relevant messages
        # from the role's complete memory. This makes the role more tool-like.
        memories = self.get_memories()
        draft_sections = [msg.instruct_content for msg in memories if isinstance(msg.instruct_content, DraftSection)]
        
        if not draft_sections:
            logger.warning("No DraftSection found in memory. Nothing to assemble.")
            return None

        logger.info(f"Assembling {len(draft_sections)} draft sections.")
        full_content_with_anchors = self._assemble_with_hashed_anchors(draft_sections)
        
        # Assuming this is the first assembly, version is 1.
        # A more complex logic could increment versions if a FullDraft already exists.
        new_draft = FullDraft(content=full_content_with_anchors, version=1)
        
        logger.info("Document assembled successfully with hashed anchors.")
        return Message(content="Full document assembled.", instruct_content=new_draft)

    def _assemble_with_hashed_anchors(self, sections: list[DraftSection]) -> str:
        """
        Assembles sections into a single document, adding a stable, content-based
        hashed anchor ID to each significant paragraph or block.
        """
        # Sort sections based on chapter_id to ensure correct order
        # Use a robust sort key, handling potential non-integer chapter_ids gracefully
        sorted_sections = sorted(sections, key=lambda s: str(s.chapter_id))
        
        full_content_parts = []
        for section in sorted_sections:
            # Split section content into paragraphs (handling multiple newlines)
            paragraphs = re.split(r'\n\s*\n', section.content.strip())
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Create a stable hash from the paragraph content
                anchor_text = para[:256] # Use a slice for performance and consistency
                anchor_id = hashlib.sha1(anchor_text.encode('utf-8')).hexdigest()[:12]
                
                # Prepend the anchor to the paragraph
                full_content_parts.append(f"[anchor-id::{anchor_id}]\n{para}")
                
        return "\n\n".join(full_content_parts)

    def _finalize_document(self, draft: FullDraft) -> str:
        """
        Removes all anchor IDs from the document for final delivery.
        """
        logger.info("Finalizing document by removing all anchor IDs.")
        # Regex to find and remove the anchor tags followed by a newline
        final_content = re.sub(r'\[anchor-id::[a-f0-9]{12}\]\n', '', draft.content)
        return final_content