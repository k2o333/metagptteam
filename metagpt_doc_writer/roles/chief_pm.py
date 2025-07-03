
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.actions.review_and_command import ReviewAndCommand
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes

class ChiefPM(Role):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Oversee the document generation process and ensure quality"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ReviewAndCommand])
        self._watch({FullDraft}) # Watches for full drafts

    async def _act(self) -> Message:
        # In a real scenario, this would be triggered by a message containing a FullDraft.
        # We would then run the ReviewAndCommand action.
        print("ChiefPM is acting...")
        # Placeholder for real implementation
        full_draft_msg = self.rc.memory.get_by_class(FullDraft)[-1]
        review_notes = await self.actions[0].run(full_draft_msg.instruct_content)
        return Message(content="Review notes generated", instruct_content=review_notes)
