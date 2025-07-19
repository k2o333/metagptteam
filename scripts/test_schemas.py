# scripts/test_schemas.py
import sys
from pathlib import Path
import json

# --- 路径设置 (关键修正) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# ----------------------------

from hierarchical.schemas import Outline, Section

def run_schema_test():
    print("--- 阶段一验收：测试数据模型 ---")

    # 1. 创建一个空的 Outline
    my_outline = Outline(goal="测试文档结构")
    print("✅ 1. Outline 创建成功")

    # 2. 添加顶级章节
    intro_section = Section(display_id="1", title="Introduction", level=1, status="COMPLETED")
    core_section = Section(display_id="2", title="Core Concepts", level=1, status="PENDING_SUBDIVIDE")
    my_outline.root_sections.extend([intro_section, core_section])
    print("✅ 2. 顶级章节添加成功")

    # 3. 为“Core Concepts”添加子章节
    sub1 = Section(display_id="2.1", title="Concept A", level=2, parent_id=core_section.section_id)
    sub2 = Section(display_id="2.2", title="Concept B", level=2, parent_id=core_section.section_id)
    core_section.sub_sections.extend([sub1, sub2])
    print("✅ 3. 子章节添加成功")

    # 4. 验证 find_section 方法
    found_section = my_outline.find_section(sub1.section_id)
    assert found_section is not None and found_section.title == "Concept A"
    print("✅ 4. find_section 方法工作正常")

    # 5. 打印最终的JSON结构以供人工检查
    print("\n--- 最终Outline结构 (JSON) ---")
    print(my_outline.model_dump_json_pretty())
    print("\n--- 验收标准 ---")
    print("请人工检查以上JSON输出是否正确构建了树状结构。")

if __name__ == "__main__":
    run_schema_test()