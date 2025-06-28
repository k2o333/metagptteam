from metagpt_doc_writer.roles.doc_assembler import DocAssembler
from metagpt_doc_writer.schemas.doc_structures import DraftSection, FullDraft

def test_doc_assembler():
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

if __name__ == "__main__":
    test_doc_assembler()
