# 文件路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/generate_changeset.py (已修正)

import json
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from typing import ClassVar # <-- 【关键】导入ClassVar
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet

# 【关键修正】: 使用 ClassVar 注解
CHANGESET_PROMPT: ClassVar[str] = """
You are a precise instruction conversion assistant. Your task is to convert a director's natural language review notes into a structured JSON `ChangeSet`.

**RULES:**
1.  **USE HASHED ANCHORS**: You MUST use the `[anchor-id::...]` tags from the document for positioning. The anchor_id is the 12-character hex string.
2.  **OPERATIONS**: Supported operations are `REPLACE_BLOCK`, `INSERT_AFTER`, `DELETE_SECTION`.
3.  **OUTPUT**: Respond ONLY with a valid JSON object. Do not add any other text or explanations.

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
            data_dict = OutputParser.parse_code(text=response_json_str)
            if isinstance(data_dict, str):
                data_dict = json.loads(data_dict)
            
            changeset = ValidatedChangeSet(**data_dict)
            logger.info(f"Successfully generated and validated changeset with {len(changeset.changes)} changes.")
            return changeset

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse LLM output into a valid ChangeSet. Error: {e}. Output:\n---\n{response_json_str}\n---")
            return ValidatedChangeSet(changes=[])