
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from metagpt.schema import Message
from metagpt.context import Context
from metagpt.roles.role import RoleContext
from metagpt_doc_writer.roles.task_dispatcher import TaskDispatcher
from metagpt_doc_writer.roles.task_refiner import TaskRefiner
from metagpt_doc_writer.schemas.doc_structures import ModuleOutline, InitialTask, RefinedTask

async def main():
    # Mock the LLM creation to prevent actual LLM initialization errors
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    # Mock _aask method for actions with AsyncMock
    mock_llm_instance.aask = AsyncMock(side_effect=[
        # Response for GenerateInitialTask
        Mock(content="Initial Task: Introduction to MetaGPT"),
        # Response for RefineTask
        Mock(content='''
        {
            "chapter_title": "Refined Introduction to MetaGPT",
            "context": "This section provides an overview of MetaGPT, its core concepts, and its architecture.",
            "goals": ["Explain MetaGPT's purpose", "Describe key components"],
            "acceptance_criteria": ["Clear definition of MetaGPT", "Accurate description of architecture"]
        }
        ''')
    ])
    # Mock parse_json method for LLM
    mock_llm_instance.parse_json = Mock(side_effect=[
        # Response for RefineTask's parse_json
        {
            "chapter_title": "Refined Introduction to MetaGPT",
            "context": "This section provides an overview of MetaGPT, its core concepts, and its architecture.",
            "goals": ["Explain MetaGPT's purpose", "Describe key components"],
            "acceptance_criteria": ["Clear definition of MetaGPT", "Accurate description of architecture"]
        }
    ])
    # Patch the llm_with_cost_manager_from_llm_config method in Context
    mocker_patch = patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)
    mocker_patch.start() # Start the patch

    # Create a mock RoleContext and add the initial message to its memory
    mock_rc_memory = Mock()
    mock_rc_memory.get_by_class.return_value = [Message(content="", instruct_content=ModuleOutline(module_title="Introduction to MetaGPT", chapters=["Chapter 1", "Chapter 2"]))]

    # Create instances of the roles
    dispatcher = TaskDispatcher()
    refiner = TaskRefiner()

    # Manually set the mocked RoleContext memory for each role
    dispatcher.rc.memory = mock_rc_memory
    refiner.rc.memory = mock_rc_memory

    # Run the dispatcher
    initial_task_msg = await dispatcher._act()
    print("Initial Task:", initial_task_msg.instruct_content)

    # Add the initial task to memory for the refiner
    # We need to ensure the mock_rc_memory returns this new message for the refiner's subsequent call
    mock_rc_memory.get_by_class.return_value = [initial_task_msg]

    # Run the refiner
    refined_task_msg = await refiner._act()
    print("Refined Task:", refined_task_msg.instruct_content)

    mocker_patch.stop() # Stop the patch

if __name__ == "__main__":
    asyncio.run(main())
