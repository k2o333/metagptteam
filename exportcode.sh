#!/bin/bash

BASE_DIR="/root/metagpt/mghier"
OUTPUT_FILE="${BASE_DIR}/research_system_codebase.md"

# 清空或创建新文件
echo "# Research System Codebase Documentation" > "$OUTPUT_FILE"
echo "Generated on $(date)" >> "$OUTPUT_FILE"

# 文件列表
FILES=(
    "${BASE_DIR}/hierarchical/actions/research_controller.py"
    "${BASE_DIR}/hierarchical/actions/research.py"
    "${BASE_DIR}/hierarchical/roles/change_coordinator.py"
    "${BASE_DIR}/hierarchical/roles/base_role.py"
    "${BASE_DIR}/hierarchical/actions/research_service.py"
    "${BASE_DIR}/mcp/manager.py"
    "${BASE_DIR}/mcp/client.py"
    "${BASE_DIR}/scripts/adapt_document.py"
    "${BASE_DIR}/configs/local_config.yaml"
)

for FILE in "${FILES[@]}"; do
    if [[ -f "$FILE" ]]; then
        # 相对路径
        REL_PATH="${FILE#$BASE_DIR/}"
        
        # 添加文件标题（使用单引号避免解析问题）
        printf '\n## File: %s\n\n' "$REL_PATH" >> "$OUTPUT_FILE"
        
        # 修复点：用单引号包裹代码块标记
        if [[ "$FILE" == *.yaml ]]; then
            echo '```yaml' >> "$OUTPUT_FILE"  # 单引号包裹
        else
            echo '```python' >> "$OUTPUT_FILE" # 单引号包裹
        fi
        
        # 写入文件内容
        cat "$FILE" >> "$OUTPUT_FILE"
        
        # 修复点：用单引号包裹结束标记
        printf '\n```\n' >> "$OUTPUT_FILE"  # 单引号包裹
    else
        echo "警告: 文件不存在 - $FILE" >&2
    fi
done

printf '\n输出文件已成功创建: %s\n' "$OUTPUT_FILE"