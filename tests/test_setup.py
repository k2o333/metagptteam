
def test_import():
    # 简单验证包是否可以被成功导入
    from metagpt_doc_writer import schemas
    assert schemas is not None
