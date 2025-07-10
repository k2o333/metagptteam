# /root/metagpt/mgfr/create_actions.py
import os
from pathlib import Path

# --- 配置 ---
ACTIONS_DIR = Path("./metagpt_doc_writer/actions")

# 根据之前的日志和通用文档流程，定义所有可能用到的Action
# 将类名和文件名统一
ACTIONS_TO_CREATE = [
    "DefineScope",
    "CreateOutline",
    "WriteSection",
    "WriteCode",
    "ReviewAndEdit",
    "FinalizeDocument",
    "Research",
    "GeneratePRD",
    "ReviewDocument",
    "GenerateDocument",
    "ReviewAndCommand", # 这个是之前版本用的，也加上以防万一
]

# Action占位符模板
ACTION_TEMPLATE = """
from metagpt.actions import Action
from metagpt.logs import logger

class {class_name}(Action):
    \"\"\"一个 {class_name} 的占位符Action。\"\"\"
    async def run(self, instruction: str = "", *args, **kwargs) -> str:
        logger.info(f"正在执行 {class_name}，指令: {{instruction}}")
        # 真实场景中，这里会与LLM交互。现在只返回一个简单的字符串。
        return f"任务 '{class_name}' 已根据指令 '{{instruction}}' 完成。"
"""

def main():
    # 确保actions目录存在
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 确保__init__.py存在
    init_file = ACTIONS_DIR / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"创建了: {init_file}")

    # 遍历并创建所有Action文件
    for action_name in ACTIONS_TO_CREATE:
        # 将驼峰命名转换为下划线命名作为文件名
        file_name = ''.join(['_' + i.lower() if i.isupper() else i for i in action_name]).lstrip('_') + '.py'
        file_path = ACTIONS_DIR / file_name
        
        # 只有当文件不存在时才创建，避免覆盖已有文件
        if not file_path.exists():
            class_content = ACTION_TEMPLATE.format(class_name=action_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(class_content)
            print(f"创建了占位符Action: {file_path}")
        else:
            print(f"文件已存在，跳过: {file_path}")

if __name__ == "__main__":
    main()