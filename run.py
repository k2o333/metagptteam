
import asyncio
from metagpt.team import Team
from metagpt.schema import Message
from metagpt_doc_writer.roles.chief_pm import ChiefPM
from metagpt_doc_writer.roles.task_dispatcher import TaskDispatcher
from metagpt_doc_writer.roles.task_refiner import TaskRefiner
from metagpt_doc_writer.roles.technical_writer import TechnicalWriter
from metagpt_doc_writer.roles.doc_assembler import DocAssembler
from metagpt_doc_writer.roles.changeset_generator import ChangeSetGenerator
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import ProjectPlan

async def main(idea: str):
    """
    This is a simplified orchestration. A real implementation would be more complex,
    with more sophisticated message passing and state management.
    """
    team = Team()
    team.hire([
        ChiefPM(),
        TaskDispatcher(),
        TaskRefiner(),
        TechnicalWriter(),
        DocAssembler(),
        ChangeSetGenerator(),
        DocModifier(),
    ])

    # For this simplified test, we'll manually pass messages
    # In a real scenario, the Team would manage the message flow based on role subscriptions
    team.run_project(idea)
    await team.run()

if __name__ == "__main__":
    asyncio.run(main("Write a simple tutorial about pytest."))
