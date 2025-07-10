import asyncio
from metagpt.team import Team
from metagpt.schema import Message
from metagpt_doc_writer.roles.chief_pm import ChiefPM
from metagpt_doc_writer.roles.changeset_generator import ChangeSetGenerator
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes

async def main():
    # This script simulates the revision loop
    
    # 1. Initial Draft
    initial_draft = FullDraft(
        content="[anchor-id::intro]This is the introduction.\n\n[anchor-id::body]This is the body.",
        version=1
    )
    
    # 2. ChiefPM reviews and creates notes
    chief_pm = ChiefPM()
    review_notes = await chief_pm.actions[0].run(initial_draft)
    
    # 3. ChangeSetGenerator creates a changeset
    changeset_generator = ChangeSetGenerator()
    validated_changeset = await changeset_generator.actions[0].run(review_notes, initial_draft)
    
    # 4. DocModifier applies the changes
    doc_modifier = DocModifier()
    
    # Manually create messages for the modifier to process
    changeset_msg = Message(content="Validated changeset", instruct_content=validated_changeset)
    draft_msg = Message(content="Initial draft", instruct_content=initial_draft)
    
    # The DocModifier's _act method needs to be called within a role context,
    # so we'll simulate that by adding messages to its memory and calling it.
    doc_modifier.rc.memory.add(changeset_msg)
    doc_modifier.rc.memory.add(draft_msg)
    
    modified_draft_msg = await doc_modifier._act()
    
    print("Original Draft:")
    print(initial_draft.content)
    print("\nModified Draft:")
    print(modified_draft_msg.instruct_content.content)

if __name__ == "__main__":
    asyncio.run(main())
