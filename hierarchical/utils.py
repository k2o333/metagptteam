# hierarchical/utils.py
from typing import Dict, Any, List, Optional
from hierarchical.schemas import Outline, Section

def build_context_for_writing(outline: Outline, target_section_id: str) -> Dict[str, Any]:
    """
    为给定的目标章节，构建一个最小化但信息充分的上下文。
    Constructs a minimal yet informative context for a given target section.
    """
    target_section = outline.find_section(target_section_id)
    if not target_section:
        return {}

    # 1. 获取父章节内容 (Parent's Full Content)
    parent_content = ""
    parent_section = None
    if target_section.parent_id:
        parent_section = outline.find_section(target_section.parent_id)
        if parent_section:
            parent_content = parent_section.content

    # 2. 获取兄弟章节标题 (Sibling Titles)
    sibling_titles = []
    if parent_section:
        for sibling in parent_section.sub_sections:
            # 只添加在当前章节之前的兄弟章节标题，模拟写作流程
            if sibling.section_id != target_section_id and sibling.display_id < target_section.display_id:
                sibling_titles.append(f"{sibling.display_id} {sibling.title}")
    
    # 3. 构建面包屑路径 (Ancestor Path / Breadcrumbs)
    breadcrumbs_list = []
    current = target_section
    while current:
        breadcrumbs_list.insert(0, f"{'  ' * (current.level - 1)}- {current.display_id} {current.title}")
        if current.parent_id:
            current = outline.find_section(current.parent_id)
        else:
            break
    
    # 将当前正在写的章节标记出来 (确保列表不为空)
    if breadcrumbs_list:
        breadcrumbs_list[-1] = f"{breadcrumbs_list[-1]} <-- YOU ARE HERE"

    return {
        "goal": outline.goal,
        "target_section_title": target_section.title,
        "parent_content": parent_content,
        "sibling_titles": "\n".join(sibling_titles) if sibling_titles else "None",
        "breadcrumbs": "\n".join(breadcrumbs_list),
    }

# 【核心新增】分层 LLM 调度辅助函数
def get_llm_pool_for_action(role_name: str, action_name: str, strategy_config: dict) -> List[str]:
    """
    根据策略配置，为给定的 Role-Action 组合确定 LLM 资源池。
    优先级: Role-Action 池 > Role 默认池。
    """
    role_action_pools = strategy_config.get("role_action_pools", {})
    role_default_pools = strategy_config.get("role_default_pools", {})
    
    # 1. 最高优先级：Role-Action 特定池
    action_key = f"{role_name}-{action_name}"
    if action_key in role_action_pools:
        return role_action_pools[action_key]
        
    # 2. 次高优先级：Role 默认池
    if role_name in role_default_pools:
        return role_default_pools[role_name]
        
    # 3. 如果都没有配置，返回空列表
    return []