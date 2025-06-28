
import asyncio
from metagpt.schema import Message
from metagpt.context import Context
from metagpt_doc_writer.roles.task_dispatcher import TaskDispatcher
from metagpt_doc_writer.roles.task_refiner import TaskRefiner
from metagpt_doc_writer.schemas.doc_structures import ModuleOutline

async def main():
    # Create a mock context and memory
    ctx = Context()
    ctx.memory.add(Message(content="", instruct_content=ModuleOutline(module_title="Introduction to MetaGPT")))

    # Create instances of the roles
    dispatcher = TaskDispatcher()
    refiner = TaskRefiner()

    # Inject the context
    dispatcher.rc.memory = ctx.memory
    refiner.rc.memory = ctx.memory

    # Run the dispatcher
    initial_task_msg = await dispatcher._act()
    print("Initial Task:", initial_task_msg.instruct_content)

    # Add the initial task to memory for the refiner
    ctx.memory.add(initial_task_msg)

    # Run the refiner
    refined_task_msg = await refiner._act()
    print("Refined Task:", refined_task_msg.instruct_content)

if __name__ == "__main__":
    asyncio.run(main())
