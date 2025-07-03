
from unittest.mock import Mock
from metagpt_doc_writer.roles.doc_assembler import DocAssembler
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft

def test_assemble_document_with_anchors(mocker):
    # Mock the LLM creation to prevent actual LLM initialization errors
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    mocker.patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)

    assembler = DocAssembler()
    sections = [
        DraftSection(chapter_id="1", content="Content A."),
        DraftSection(chapter_id="2", content="Content B.")
    ]
    # 模拟输入并调用内部方法
    result = assembler._assemble_with_anchors(sections)
    assert "[anchor-id::" in result
    assert "Content A." in result
    assert "Content B." in result

def test_finalize_document(mocker):
    # Mock the LLM creation to prevent actual LLM initialization errors
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    mocker.patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)

    assembler = DocAssembler()
    content_with_anchors = "[anchor-id::abc]Content A.[anchor-id::def]Content B."
    draft = FullDraft(content=content_with_anchors)
    result = assembler._finalize_document(draft)
    assert "[anchor-id::" not in result
    assert "Content A." in result
    assert "Content B." in result
