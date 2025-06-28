
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, Change

def validate_schema():
    data = {
        "changes": [
            {"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "Hello", "comment": "Test"}
        ]
    }
    try:
        instance = ValidatedChangeSet(**data)
        print("Schema validation successful!")
        print(instance)
    except Exception as e:
        print(f"Schema validation failed: {e}")

if __name__ == "__main__":
    validate_schema()
