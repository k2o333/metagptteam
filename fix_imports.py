# /root/metagpt/mgfr/fix_imports.py (精确目标版)

import os
from pathlib import Path
import re

# --- 配置 ---
PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR_NAME = "metagpt_doc_writer"

# --- 修正: 明确指定只扫描 'roles' 和 'actions' 这两个子目录 ---
TARGET_SUBDIRS = ["roles", "actions"]

# 定义要查找和替换的模式
# 这个正则表达式会查找所有以 "from metagpt_doc_writer" 或 "import metagpt_doc_writer" 开头的行
FIND_PATTERN = re.compile(r"(from|import)\s+(metagpt_doc_writer[\.\w]*)")
REPLACE_WITH = r"\1 mgfr.\2"

def fix_imports_in_file(file_path: Path):
    """
    读取一个文件，修正导入语句，然后写回。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用 re.sub 进行查找和替换
        new_content, num_replacements = FIND_PATTERN.subn(REPLACE_WITH, content)

        if num_replacements > 0:
            print(f"  [+] 已修正 '{file_path.relative_to(PROJECT_ROOT)}' 文件中的 {num_replacements} 处导入。")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        # 如果不需要显示未修改的文件，可以注释掉下面的 else 块
        # else:
        #     print(f"  [-] 文件 '{file_path.relative_to(PROJECT_ROOT)}' 无需修改。")

    except Exception as e:
        print(f"  [!] 处理文件 {file_path} 时发生错误: {e}")

def main():
    """
    主函数，遍历指定的目标目录并修复所有Python文件。
    """
    print("--- 开始扫描并修正 'roles' 和 'actions' 目录下的导入语句 ---")
    
    total_files_processed = 0
    
    # 遍历我们指定的目标子目录
    for subdir in TARGET_SUBDIRS:
        target_path = PROJECT_ROOT / BASE_DIR_NAME / subdir
        
        if not target_path.is_dir():
            print(f"[警告] 目标目录不存在，跳过: {target_path}")
            continue
            
        print(f"\n正在扫描目录: {target_path.relative_to(PROJECT_ROOT)}/")
        
        # 使用 os.walk 递归地遍历所有子目录和文件
        for root, _, files in os.walk(target_path):
            for filename in files:
                if filename.endswith(".py"):
                    file_path = Path(root) / filename
                    fix_imports_in_file(file_path)
                    total_files_processed += 1
    
    print(f"\n--- 扫描完成。共处理了 {total_files_processed} 个 Python 文件。---")
    print("现在可以重新运行你的主程序了。")

if __name__ == "__main__":
    main()