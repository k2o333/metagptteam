# 精确文档改编工作流增强功能说明

## 功能概述

本增强功能解决了原有文档改编工作流中LLM提供位置索引不准确导致文本替换错误的问题。通过引入精确定位Agent，确保每次文本修改都能准确找到目标位置。

## 核心组件

### 1. TextLocationAgent (精确定位代理)
- **基于**: MetaGPT的RoleZero框架
- **职责**: 精确验证和定位文档中的文本位置
- **工具**: 集成MetaGPT的Editor工具

### 2. ConfirmTextLocation Action (确认位置动作)
- **功能**: 使用代码工具精确查找文本位置
- **策略**: 
  - 直接精确搜索
  - 近似位置附近搜索
  - 模糊匹配搜索
- **输出**: 精确位置信息和上下文内容

### 3. 集成到ChangeCoordinator (变更协调器)
- **新增步骤**: 在发送重写任务前增加位置验证步骤
- **验证流程**: LLM位置 → 精确定位Agent验证 → ChiefPM处理

## 工作流程

```
1. 用户请求文档改编
   ↓
2. ChangeCoordinator分析变更
   ↓
3. 发送位置验证请求到TextLocationAgent
   ↓
4. TextLocationAgent使用ConfirmTextLocation精确定位
   ↓
5. 返回精确位置给ChangeCoordinator
   ↓
6. ChangeCoordinator发送精确位置到ChiefPM
   ↓
7. 正常处理后续改编流程
```

## 技术特点

### 精确定位策略
1. **直接搜索**: 完全匹配搜索文本
2. **近似搜索**: 在LLM提供的近似位置附近搜索
3. **模糊匹配**: 使用正则表达式处理文本变化
4. **上下文验证**: 提供目标位置周围的上下文内容

### 错误处理
- 定位失败时回退到原始LLM提供的位置
- 详细的错误日志和调试信息
- 位置验证失败的明确提示

## 使用效果

### 增强前问题
- LLM索引错误导致文本替换位置偏差
- 文档内容损坏和重复
- 替换文本拼接错误

### 增强后效果
- ✅ 精确的文本定位（行号和字符位置）
- ✅ 正确的上下文验证
- ✅ 防止文档内容损坏
- ✅ 提高改编成功率

## 测试验证

运行测试脚本验证功能：
```bash
# 测试精确定位功能
python /root/metagpt/mghier/test_precise_location.py

# 测试完整工作流集成
python /root/metagpt/mghier/test_workflow_integration.py
```

## 文件结构

```
/root/metagpt/mghier/
├── hierarchical/agents/
│   └── text_location_agent.py     # 精确定位Agent实现
├── hierarchical/roles/
│   └── change_coordinator.py      # 集成位置验证的协调器
├── scripts/
│   └── adapt_document.py          # 更新团队配置
├── test_precise_location.py       # 精确定位测试
└── test_workflow_integration.py   # 工作流集成测试
```

## 性能影响

- 增加一次Agent间通信延迟
- 提高文本替换准确性
- 减少因位置错误导致的重试
- 整体成功率显著提升