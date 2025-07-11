# 路径: /root/metagpt/mgfr/scripts/test_doc_modifier.py (新增文件)

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- 导入待测试模块和依赖 ---
from metagpt.schema import Message
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, FullDraft, Change


def setup_modifier_with_memory(original_content: str, changes: list) -> DocModifier:
    """一个辅助函数，用于创建一个带有预设记忆的DocModifier实例。"""
    
    # 使用Mocker来模拟LLM，因为基类Role在初始化时需要它
    with patch('metagpt.roles.role.Role.llm', new_callable=Mock):
        modifier = DocModifier()

    # 准备模拟消息并添加到角色的记忆中
    original_draft = FullDraft(content=original_content)
    modifier.rc.memory.add(Message(content="Original Draft", instruct_content=original_draft))

    validated_changeset = ValidatedChangeSet(changes=changes)
    modifier.rc.memory.add(Message(content="Validated Changeset", instruct_content=validated_changeset))

    return modifier


async def test_doc_modifier():
    """测试DocModifier的核心功能：替换、插入、删除。"""
    print("--- 启动 DocModifier 单元测试 ---")

    # 1. 准备原始文档内容
    original_doc = (
        "[anchor-id::intro]## 1. Introduction\nThis is the intro section.\n\n"
        "[anchor-id::main-body]## 2. Main Body\nThis content needs an update.\n\n"
        "[anchor-id::to-delete]## 3. Obsolete Section\nThis part should be removed.\n\n"
        "[anchor-id::conclusion]## 4. Conclusion\nThis is the end."
    )
    
    # 2. 定义修改指令
    changes_to_apply = [
        # 指令1: 替换 main-body 的内容
        Change(operation="REPLACE_BLOCK", anchor_id="main-body", new_content="## 2. Main Body\nThis is the UPDATED content.\n\n", comment="Update main body content"),
        # 指令2: 在 intro 后面插入新章节
        Change(operation="INSERT_AFTER", anchor_id="intro", new_content="[anchor-id::new-feature]## 1.5. New Feature\nThis is a newly inserted section.\n\n", comment="Add new feature section after intro"),
        # 指令3: 删除 to-delete 章节
        Change(operation="DELETE_SECTION", anchor_id="to-delete", comment="Delete the obsolete section 3"),
        # 指令4: 尝试修改一个不存在的锚点（应该被忽略）
        Change(operation="REPLACE_BLOCK", anchor_id="non-existent-anchor", new_content="This should not appear.", comment="Attempt to modify non-existent anchor"),
    ]

    # 3. 创建带有预设记忆的Modifier实例
    modifier = setup_modifier_with_memory(original_doc, changes_to_apply)

    # 4. 执行_act方法
    print("\n原始文档:\n" + "="*20 + f"\n{original_doc}")
    result_message = await modifier._act()
    
    # 5. 验证结果
    assert result_message is not None, "执行act后应返回一个消息"
    
    modified_draft = result_message.instruct_content
    assert isinstance(modified_draft, FullDraft), "返回的消息内容应为FullDraft类型"
    
    modified_content = modified_draft.content
    print("\n修改后文档:\n" + "="*20 + f"\n{modified_content}")

    # 断言：检查修改是否正确应用
    assert "This is the UPDATED content." in modified_content, "REPLACE_BLOCK 失败"
    assert "This content needs an update." not in modified_content, "REPLACE_BLOCK 未能移除旧内容"
    
    assert "## 1.5. New Feature" in modified_content, "INSERT_AFTER 失败"
    
    assert "## 3. Obsolete Section" not in modified_content, "DELETE_SECTION 失败"
    
    assert "This should not appear." not in modified_content, "不应修改不存在的锚点"
    
    assert modified_draft.version == 2, "版本号应该增加"

    print("\n--- DocModifier 单元测试通过！ ---\n")

if __name__ == "__main__":
    asyncio.run(test_doc_modifier())