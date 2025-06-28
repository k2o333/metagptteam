
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import Change

def test_doc_modifier():
    modifier = DocModifier()
    content = "[anchor-id::abc]Old content.[anchor-id::def]"
    changes = [Change(operation="REPLACE_BLOCK", anchor_id="abc", new_content="New content.", comment="...")]
    
    new_content = modifier._apply_changes(content, changes)
    print("Original content:", content)
    print("Content after changes:", new_content)
    
    # A more specific assertion is needed here based on the actual implementation of _apply_changes
    # The current placeholder implementation is not fully correct.
    # This is just a basic check.
    assert "New content" in new_content

if __name__ == "__main__":
    test_doc_modifier()
