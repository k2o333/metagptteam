from unittest.mock import patch, PropertyMock, Mock
from metagpt_doc_writer.roles.doc_assembler import DocAssembler
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft
import uuid

def test_doc_assembler():
    """
    Tests the deterministic logic of DocAssembler.
    """
    # Mock the LLM property on the Role class to prevent actual LLM initialization errors
    with patch('metagpt.roles.role.Role.llm', new_callable=PropertyMock) as mock_llm_property:
        # Configure the mock to return a dummy object that has a 'system_prompt' attribute
        mock_llm_instance = Mock()
        mock_llm_instance.system_prompt = ""
        mock_llm_property.return_value = mock_llm_instance

        assembler = DocAssembler()
        sections = [
            DraftSection(chapter_id="1", content="Content A."),
            DraftSection(chapter_id="2", content="Content B.")
        ]

        # Test assembling with anchors
        assembled_content = assembler._assemble_with_anchors(sections)
        print("Assembled content with anchors:")
        print(assembled_content)
        assert "[anchor-id::" in assembled_content
        assert "Content A." in assembled_content
        assert "Content B." in assembled_content

        # Test finalizing document
        draft = FullDraft(content=assembled_content)
        final_content = assembler._finalize_document(draft)
        print("\nFinalized content:")
        print(final_content)
        assert "[anchor-id::" not in final_content
        assert "Content A." in final_content
        assert "Content B." in final_content
        print("\nDocAssembler script validation successful!")

if __name__ == "__main__":
    test_doc_assembler()