import pytest

def test_prompt_safety():
    """验证模板字符串不会在导入时抛出异常"""
    from metagpt_doc_writer.prompts import self_reflection_prompt
    assert "$request" in self_reflection_prompt.SELF_REFLECTION_PROMPT_TEMPLATE.template
    assert "$output" in self_reflection_prompt.SELF_REFLECTION_PROMPT_TEMPLATE.template
