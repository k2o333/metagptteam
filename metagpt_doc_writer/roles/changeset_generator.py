# /root/metagpt/mgfr/metagpt_doc_writer/roles/changeset_generator.py

from .base_role import MyBaseRole
from metagpt.schema import Message
from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, ValidatedChangeSet, FullDraft

class ChangeSetGenerator(MyBaseRole):
    name: str = "ChangeSetGenerator"
    profile: str = "ChangeSet Generator"
    goal: str = "Convert natural language review notes into a validated changeset."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateChangeSet])
        self._watch({ReviewNotes})

    async def _act(self) -> Message:
        # Correctly filter messages from memory
        memories = self.get_memories()
        review_notes_msg = [m for m in memories if isinstance(m.instruct_content, ReviewNotes)][-1]
        full_draft_msg = [m for m in memories if isinstance(m.instruct_content, FullDraft)][-1]
        
        validated_changeset = await self.actions[0].run(
            review_notes=review_notes_msg.instruct_content,
            full_draft=full_draft_msg.instruct_content
        )
        
        return Message(content="Validated changeset generated", instruct_content=validated_changeset)