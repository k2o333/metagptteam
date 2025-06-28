
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, Change

def test_validated_changeset_creation():
    data = {
        "changes": [
            {"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "Hello", "comment": "Test"}
        ]
    }
    # 验证数据可以被成功解析为Pydantic模型
    instance = ValidatedChangeSet(**data)
    assert len(instance.changes) == 1
    assert instance.changes[0].operation == "REPLACE_BLOCK"
