
import asyncio
from metagpt.schema import Message
from metagpt.context import Context
from metagpt_doc_writer.roles.technical_writer import TechnicalWriter
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, RefinedTask

async def main():
    # Create a mock context and memory
    ctx = Context()
    refined_task = RefinedTask(
        chapter_title="Test Chapter",
        context="Test context",
        goals=["Goal 1"],
        acceptance_criteria=["Criterion 1"]
    )
    approved_task = ApprovedTask(chapter_title="Test Chapter", refined_task=refined_task)
    ctx.memory.add(Message(content="", instruct_content=approved_task))

    # Create an instance of the role
    writer = TechnicalWriter()

    # Inject the context
    writer.rc.memory = ctx.memory

    # Run the writer
    draft_section_msg = await writer._act()
    print("Draft Section:", draft_section_msg.instruct_content)

if __name__ == "__main__":
    asyncio.run(main())
