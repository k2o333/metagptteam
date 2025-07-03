
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, DraftSection

class TechnicalWriter(Role):
    name: str = "TechnicalWriter"
    profile: str = "Technical Writer"
    goal: str = "Write high-quality technical documentation"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Pass the LLM instance to the WriteSection action
        self.set_actions([WriteSection(llm=self.llm)])
        self._watch({ApprovedTask}) # Watches for approved tasks

    async def _act(self) -> Message:
        # In a real scenario, this would be triggered by a message containing an ApprovedTask.
        # We would then run the WriteSection action.
        print("TechnicalWriter is acting...")
        # Placeholder for real implementation
        approved_task_msg = self.rc.memory.get_by_class(ApprovedTask)[-1]
        draft_section = await self.actions[0].run(approved_task_msg.instruct_content)
        return Message(content="Draft section written", instruct_content=draft_section)
