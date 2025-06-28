
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet

class ChangeSetGenerator(Role):
    def __init__(self, name="ChangeSetGenerator", profile="ChangeSet Generator", goal="Generate validated change sets from review notes", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([GenerateChangeSet])
        self._watch({ReviewNotes}) # Watches for review notes

    async def _act(self) -> Message:
        # In a real scenario, this would be triggered by a message containing ReviewNotes.
        # We would then run the GenerateChangeSet action.
        print("ChangeSetGenerator is acting...")
        # Placeholder for real implementation
        review_notes_msg = self.rc.memory.get_by_class(ReviewNotes)[-1]
        full_draft_msg = self.rc.memory.get_by_class(FullDraft)[-1] # Assumes draft is in memory
        validated_changeset = await self.actions[0].run(review_notes_msg.instruct_content, full_draft_msg.instruct_content)
        return Message(content="Validated changeset generated", instruct_content=validated_changeset)
