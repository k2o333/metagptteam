
import asyncio
from metagpt.schema import Message
from metagpt.context import Context
from metagpt_doc_writer.roles.chief_pm import ChiefPM
from metagpt_doc_writer.roles.changeset_generator import ChangeSetGenerator
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import FullDraft

async def main():
    # Create a mock context and memory
    ctx = Context()
    draft_content = "[anchor-id::anc123]This is the original content that needs to be made more concise."
    ctx.memory.add(Message(content="", instruct_content=FullDraft(content=draft_content)))

    # Create instances of the roles
    chief_pm = ChiefPM()
    changeset_generator = ChangeSetGenerator()
    doc_modifier = DocModifier()

    # Inject the context
    chief_pm.rc.memory = ctx.memory
    changeset_generator.rc.memory = ctx.memory
    doc_modifier.rc.memory = ctx.memory

    # Run the ChiefPM
    review_notes_msg = await chief_pm._act()
    print("Review Notes:", review_notes_msg.instruct_content)
    ctx.memory.add(review_notes_msg)

    # Run the ChangeSetGenerator
    changeset_msg = await changeset_generator._act()
    print("Validated ChangeSet:", changeset_msg.instruct_content)
    ctx.memory.add(changeset_msg)

    # Run the DocModifier
    # The DocModifier's _act method is a placeholder, so we call _apply_changes directly for this test
    new_draft_content = doc_modifier._apply_changes(draft_content, changeset_msg.instruct_content.changes)
    print("New Draft Content:", new_draft_content)

if __name__ == "__main__":
    asyncio.run(main())
