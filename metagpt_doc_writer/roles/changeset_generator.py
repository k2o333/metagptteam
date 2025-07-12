# /root/metagpt/mgfr/metagpt_doc_writer/roles/changeset_generator.py (原生重构版)

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger

from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet
from metagpt_doc_writer.actions.review_and_command import ReviewAndCommand # 用于监听
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet

class ChangeSetGenerator(DocWriterBaseRole):
    name: str = "ChangeSetGenerator"
    profile: str = "Instruction Engineer"
    goal: str = "Accurately convert natural language feedback into a machine-executable changeset."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateChangeSet])
        # 监听 ChiefPM 的 ReviewAndCommand 行动产出的 ReviewNotes
        self._watch([ReviewAndCommand])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo.name}")
        
        # 输入是 ReviewNotes，但它需要 FullDraft 作为上下文
        review_notes_msg = self.rc.history[-1]
        try:
            # 从记忆中找到最近的 FullDraft
            full_draft_msg = next(m for m in reversed(self.rc.memory.get()) if isinstance(m.instruct_content, FullDraft))
        except StopIteration:
            logger.error("Could not find FullDraft in memory for generating changeset.")
            return Message(content="Error: No FullDraft found to apply changes to.", role=self.profile)

        validated_changeset = await self.rc.todo.run(
            review_notes=review_notes_msg.instruct_content,
            full_draft=full_draft_msg.instruct_content
        )
        
        return Message(
            content=f"Generated changeset with {len(validated_changeset.changes)} changes.",
            instruct_content=validated_changeset,
            cause_by=type(self.rc.todo)
        )