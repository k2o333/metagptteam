# 路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/generate_changeset.py

import json
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet, Change
from metagpt.utils.common import OutputParser
from typing import ClassVar

CHANGESET_PROMPT: ClassVar[str] = """
You are a precise instruction conversion assistant. Your task is to convert a director's natural language review notes into a structured JSON `ChangeSet`.

**RULES:**
1.  **USE HASHED ANCHORS**: You MUST use the `[anchor-id::...]` tags from the document for positioning.
2.  **OPERATIONS**: Supported operations are `REPLACE_BLOCK`, `INSERT_AFTER`, `DELETE_SECTION`.
3.  **OUTPUT**: Respond ONLY with a valid JSON object. Do not add any other text.

**Director's Review Notes**:
---
{review_notes}
---

**Original Document (with anchors for context)**:
---
{draft_content}
---

**Your JSON `ChangeSet`**:
"""

class GenerateChangeSet(Action):
    """
    An action to convert natural language feedback into a structured ChangeSet.
    """
    async def run(self, review_notes: ReviewNotes, full_draft: FullDraft) -> ValidatedChangeSet:
        logger.info("Generating changeset from review notes...")
        
        prompt = CHANGESET_PROMPT.format(
            review_notes=review_notes.feedback,
            draft_content=full_draft.content
        )
        
        response_json_str = await self._aask(prompt)
        
        try:
            # Use MetaGPT's parser which is more robust
            data_dict = OutputParser.parse_code(block=None, text=response_json_str)
            if isinstance(data_dict, str):
                data_dict = json.loads(data_dict) # Fallback if it's a plain string
            
            # Here we can add validation logic in the future
            changeset = ValidatedChangeSet(**data_dict)
            logger.info(f"Successfully generated changeset with {len(changeset.changes)} changes.")
            return changeset

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse LLM output into a valid ChangeSet. Error: {e}. Output: {response_json_str}")
            # In a real scenario, this would trigger the repair loop. For now, we return empty.
            return ValidatedChangeSet(changes=[])