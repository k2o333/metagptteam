
import json
from metagpt.actions import Action
from metagpt.provider.base_llm import BaseLLM
from metagpt.utils.common import OutputParser
from pydantic import ValidationError
from metagpt.logs import logger

from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet

MAX_RETRY = 3

class GenerateChangeSet(Action):
    """
    Action to generate a validated changeset from review notes.
    Implements the validation-repair loop to ensure the output is always a valid
    ValidatedChangeSet object.
    """

    def __init__(self, name: str = "GenerateChangeSet", context=None, **kwargs):
        super().__init__(name=name, context=context, **kwargs)
        # LLM is set via self.set_llm(llm) by the Role, not directly in Action's __init__
        # LLM is set via self.set_llm(llm) by the Role, not directly in Action's __init__
        # LLM is set via self.set_llm(llm) by the Role, not directly in Action's __init__

    def _build_system_prompt(self) -> str:
        return """
        You are a precise instruction conversion assistant. Your task is to convert a product director's natural language review notes into a structured JSON `ChangeSet`.

        **IMPORTANT RULES**:
        1. You MUST use 'context anchors' for positioning. Find a short, unique text snippet from the original document (`anchor_id`) to locate the modification point. NEVER use line numbers.
        2. The supported operations are: `REPLACE_BLOCK`, `INSERT_AFTER`, `DELETE_SECTION`.
        3. For `DELETE_SECTION`, you must provide both `anchor_id_start` and `anchor_id_end`.
        4. Your output MUST be a single, valid JSON object that conforms to the `ValidatedChangeSet` schema.
        """

    def _build_prompt(self, review_notes: ReviewNotes, full_draft: FullDraft) -> str:
        # For simplicity, we might only include a snippet of the draft, but for accuracy,
        # the full draft is better if context allows.
        return f"""
        **Product Director's Review Notes**:
        ---
        {review_notes.feedback}
        ---

        **Original Document for Context**:
        ---
        {full_draft.content[:4000]}
        ---

        Now, generate the `ChangeSet` JSON object.
        """

    def _build_repair_prompt(self, raw_json_str: str, error_msg: str) -> str:
        return f"""
        The previous JSON generation failed. Please fix the following JSON string.
        
        **Error**: {error_msg}
        
        **Malformed JSON**:
        ```json
        {raw_json_str}
        ```

        **Instructions**:
        - Correct the JSON syntax.
        - Ensure the structure adheres to the `ValidatedChangeSet` schema.
        - Do not repeat the error in your response.
        - Output ONLY the corrected, valid JSON object.
        """

    async def run(self, review_notes: ReviewNotes, full_draft: FullDraft) -> ValidatedChangeSet:
        """
        Executes the validation-repair loop to generate a reliable changeset.
        """
        prompt = self._build_prompt(review_notes, full_draft)
        system_prompt = self._build_system_prompt()

        for i in range(MAX_RETRY):
            try:
                # 1. Attempt to generate JSON from LLM
                raw_json_str = await self.llm.aask(prompt, system_msgs=[system_prompt])
                
                # 2. Syntactic validation (JSON format)
                changeset_dict = OutputParser.extract_struct(raw_json_str, dict)
                
                # 3. Logical validation (Pydantic schema & anchor existence)
                validated_changeset = ValidatedChangeSet(**changeset_dict)
                self._validate_anchors(validated_changeset, full_draft.content)
                
                # 4. Success
                logger.info(f"Successfully generated a valid ChangeSet on attempt {i+1}.")
                return validated_changeset

            except AnchorNotFoundException as e:
                logger.warning(f"Attempt {i+1}/{MAX_RETRY} failed: {e}. Asking LLM to correct the anchor.")
                # For anchor errors, we go back to the original prompt but add a note about the error.
                prompt = self._build_prompt(review_notes, full_draft) + f"\n\n**Previous Error**: An anchor you provided ('{e.anchor_id}') was not found. Please find a valid anchor in the document."
            
            except (json.JSONDecodeError, ValidationError, Exception) as e:
                logger.warning(f"Attempt {i+1}/{MAX_RETRY} failed: {e}. Initiating repair.")
                prompt = self._build_repair_prompt(raw_json_str, str(e))

        logger.error("Failed to generate a valid ChangeSet after multiple retries.")
        return ValidatedChangeSet(changes=[]) # Return empty set on total failure

    def _validate_anchors(self, changeset: ValidatedChangeSet, draft_content: str):
        """
        Validates that all anchors in the changeset exist in the draft.
        Raises AnchorNotFoundException if an anchor is not found.
        """
        for change in changeset.changes:
            if change.operation == "DELETE_SECTION":
                if not (hasattr(change, 'anchor_id_start') and change.anchor_id_start and \
                        hasattr(change, 'anchor_id_end') and change.anchor_id_end):
                    raise ValueError("DELETE_SECTION operation requires both anchor_id_start and anchor_id_end.")
                
                if change.anchor_id_start not in draft_content:
                    raise AnchorNotFoundException(change.anchor_id_start)
                if change.anchor_id_end not in draft_content:
                    raise AnchorNotFoundException(change.anchor_id_end)
            else:
                if change.anchor_id and change.anchor_id not in draft_content:
                    raise AnchorNotFoundException(change.anchor_id)

class AnchorNotFoundException(Exception):
    """Custom exception for when an anchor is not found in the document."""
    def __init__(self, anchor_id: str):
        self.anchor_id = anchor_id
        super().__init__(f"Anchor ID '{anchor_id}' not found in the document.")
