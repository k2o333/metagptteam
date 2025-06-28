
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.actions.generate_initial_task import GenerateInitialTask
from metagpt_doc_writer.schemas.doc_structures import ModuleOutline, InitialTask

class TaskDispatcher(Role):
    def __init__(self, name="TaskDispatcher", profile="Task Dispatcher", goal="Generate initial tasks from module outlines", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([GenerateInitialTask])
        self._watch({ModuleOutline}) # Watches for module outlines

    async def _act(self) -> Message:
        # In a real scenario, this would be triggered by a message containing a ModuleOutline.
        # We would then run the GenerateInitialTask action.
        print("TaskDispatcher is acting...")
        # Placeholder for real implementation
        module_outline_msg = self.rc.memory.get_by_class(ModuleOutline)[-1]
        initial_task = await self.actions[0].run(module_outline_msg.instruct_content.module_title)
        return Message(content="Initial task generated", instruct_content=initial_task)
