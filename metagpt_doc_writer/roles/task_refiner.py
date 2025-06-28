
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.actions.refine_task import RefineTask
from metagpt_doc_writer.schemas.doc_structures import InitialTask, RefinedTask

class TaskRefiner(Role):
    def __init__(self, name="TaskRefiner", profile="Task Refiner", goal="Refine initial tasks to make them more detailed", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([RefineTask])
        self._watch({InitialTask}) # Watches for initial tasks

    async def _act(self) -> Message:
        # In a real scenario, this would be triggered by a message containing an InitialTask.
        # We would then run the RefineTask action.
        print("TaskRefiner is acting...")
        # Placeholder for real implementation
        initial_task_msg = self.rc.memory.get_by_class(InitialTask)[-1]
        refined_task = await self.actions[0].run(initial_task_msg.instruct_content)
        return Message(content="Task refined", instruct_content=refined_task)
