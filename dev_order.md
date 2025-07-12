

### **多智能体文档撰写系统：终极演进路线 (SOP - Final Integrated Version)**

**核心指导原则 (Guiding Principles):**

*   **愿景驱动，架构先行 (Vision-Driven, Architecture-First):** 始终以`prd35.md`的最终愿景为北极星，确保每一步技术选型和实现都服务于构建一个**鲁棒、智能、可扩展**的系统。
*   **对话即调用 (Dialogue as Invocation):** 将Agent与工具的交互，从“指令-执行”模式，全面升级为“对话-响应”模式。工具不再是被动调用的函数，而是参与对话的“虚拟专家”，统一系统内的交互范式。
*   **风险前置 (De-risk First):** 优先通过**技术探针 (Spike)** 验证所有新引入的、不确定的技术点，为后续大规模开发扫清障碍。
*   **主线驱动 (Main-Thread Driven):** 聚焦于打通和强化“**规划 -> 增强 -> 执行 -> 组装 -> 修订 -> 批准**”的核心价值流，确保主干流程的健壮性。
*   **增量增强 (Incremental Enhancement):** 在主干稳定后，以“插件化”的思路逐步为Agent注入高级智能，避免主流程的过度复杂化。
*   **小步快跑，明确验收 (Small, Verifiable Steps):** 每一步都有明确、可独立验证的交付成果和可量化的验收标准。

---

### **阶段零：地基重构与核心能力验证 (Foundation Refactoring & Core Capability Verification)**

**目标:** 建立一个灵活、健壮、可配置且风险可控的底层架构，为所有高级功能的引入奠定坚实基础。

*   **第1步: 实现声明式角色LLM绑定**
    *   **理念:** **配置与代码彻底解耦。** 通过YAML文件声明式地管理角色与LLM的绑定，实现最大的灵活性和易维护性。
    *   **任务:**
        1.  **重构`configs/config2.yaml`格式:**
            ```yaml
            llms:
              - key: "strong_llm"
                api_type: "open_llm"
                model: "gpt-4o"
                # ...
              - key: "fast_llm"
                api_type: "open_llm"
                model: "gpt-4o-mini"
                # ...
            role_llm_bindings:
              "ChiefPM": "strong_llm"
              "TechnicalWriter": "fast_llm"
              # ... 其他角色绑定
            llm: # 默认LLM，用于回退
              key: "default"
              model: "gpt-4o-mini"
              # ...
            ```
        2.  **重构`Team`初始化逻辑:** 在`run.py`或`Team`类中，读取`role_llm_bindings`配置，在雇佣角色时，自动从LLM连接池中查找并注入对应的LLM实例。
    *   **验收标准:**
        *   **标准1:** `run.py`中移除所有硬编码的`Role(llm=...)`。
        *   **标准2:** 在`config2.yaml`中修改一个角色的LLM绑定，重新运行，日志能反映出变化，**无需修改任何Python代码**。

*   **第2步: 实现通用Token计数器 (Universal Token Counter)**
    *   **理念:** 成本控制和上下文管理是系统的生命线，必须依赖于一个对各类模型都相对准确的Token计数器。
    *   **任务:**
        1.  创建`UniversalTokenizer`类，内部维护`tiktoken`编码器与模型族的映射关系。
        2.  对未知模型，**默认回退到基于字符数的估算方法**（如`len(text) / 3`），并打印`warning`日志，确保系统鲁棒性。
        3.  在`metagpt.provider.base_llm.BaseLLM`中集成此`UniversalTokenizer`。
    *   **验收标准:**
        *   **标准1:** 单元测试覆盖已知模型（如GPT-4）、近似模型（如Llama3）和未知模型。
        *   **标准2:** 断言三种情况都能返回一个整数，且未知模型会触发警告日志。

*   **第3步: 【技术探针】验证核心高风险技术点**
    *   **理念:** 用最小化的脚本，快速验证所有不确定性最高的技术方案，为后续开发扫清障碍。
    *   **任务:** 创建独立的`scripts/spike_test_*.py`脚本。
        1.  **MCP基础探针 (`spike_test_mcp.py`):** 验证`llm.acompletion`能正确处理包含多角色（如`critic`）的`messages`列表，证明LLM能理解多方对话上下文。
        2.  **文档改编探针 (`spike_test_doc_adaptation.py`):** 验证`Planner`可以消费一个完整的Markdown文档作为输入，并生成与之结构相关的`ProjectPlan`。
        3.  **长上下文处理探针 (`spike_test_context_optimizer.py`):** 验证使用内存RAG（`metagGPT.rag`）能够从超长文档中，根据查询准确检索出相关的文本片段，解决上下文丢失问题。
        4.  **MCP工具调用探针 (`spike_test_mcp_tool_call.py`):** **(关键探针)** 验证将工具模拟为对话参与者（`role: "assistant", name: "ToolName_Tool"`）的可行性。证明LLM能在一个对话流中，正确理解并利用“工具角色”提供的信息来完成任务。
    *   **验收标准:** 每个探针脚本都能成功运行，并且其输出明确证明了对应技术路线的可行性（如MCP探针的LLM回复体现了多角色上下文理解，RAG探针检索出了文档末尾内容等）。

---

### **阶段一：实现鲁棒的“规划-执行-修订”核心循环**

**目标:** 将探针验证过的技术产品化，构建一个包含健壮规划、执行和修订功能的端到端主流程。

*   **第4步: 产品化文档改编流程入口**
    *   **任务:** 修改`scripts/run.py`，增加`--adapt-from-file <path>`参数，读取文件内容并传递给`Planner`。
    *   **验收标准:** 运行带此参数的命令，日志显示`Planner`生成的`ProjectPlan`与输入文档的章节结构高度相关。

*   **第5步: 实现`GroupPM`与探索式RAG规划增强**
    *   **理念:** 规划不应凭空想象，而应基于已有的知识库，提高大纲的深度和准确性。
    *   **任务:**
        1.  创建`roles/group_pm.py`和`actions/create_module_outline.py`。
        2.  `CreateModuleOutline`的`run`方法接收模块标题，先用标题`aquery()` RAG知识库，然后将检索结果和标题一同传给LLM，生成更详尽的大纲。
        3.  在`run.py`中，将`GroupPM`的执行环节插入到`Planner`之后、`TechnicalWriter`之前。
    *   **验收标准:** `TechnicalWriter`接收到的任务指令中，包含了由`GroupPM`生成的、带有RAG检索信息的`rag_hint`字段。

*   **第6步: 实现带哈希锚点的`DocAssembler`**
    *   **理念:** 锚点必须是**稳定且可调试**的。基于内容的哈希是实现可靠修订指令的基础。
    *   **任务:** 修改`DocAssembler`，使用`hashlib.sha1(paragraph_text.encode()).hexdigest()[:12]`为每个段落生成确定性的锚点ID。
    *   **验收标准:** 手动检查生成的`FullDraft`文档，确认其中包含形如`<!-- ANCHOR: a1b2c3d4e5f6 -->`的、基于内容哈希的锚点。

*   **第7步: 实现完整的、基于哈希锚点的修订循环**
    *   **理念:** 将“审阅”、“指令转换”和“执行”彻底解耦，并通过“验证-修复循环”确保修订指令的100%可靠性。
    *   **任务:**
        1.  **`ChiefPM.ReviewAndCommand`**: 实现**熔断机制**，防止无限修订循环。
        2.  **`ChangeSetGenerator`**: **(核心)** 实现包含**语法验证（`try-except json.loads`）和逻辑验证（锚点ID存在性检查）**的修复循环。若验证失败，则调用LLM进行自我修复。
        3.  **`DocModifier`**: 确认其能正确处理基于哈希锚点的`REPLACE`, `INSERT`, `DELETE`操作。
    *   **验收标准:**
        *   **标准1 (成功路径):** 模拟`ChiefPM`给出修改意见，断言最终文档被正确修改。
        *   **标准2 (修复路径):** 在测试中，mock LLM返回**格式错误**的JSON或**无效的锚点**，断言`ChangeSetGenerator`依然能成功输出，并且触发了修复流程。
        *   **标准3 (熔断路径):** 在测试中，让`ChiefPM`连续多次返回修改意见，断言达到阈值后它会强制批准，并打印警告日志。

---

### **阶段二：Agent智能与能力扩展 (Agent Intelligence & Capability Expansion)**

**目标:** 在核心流程稳定后，统一采用MCP范式，为Agent注入高级智能，使其从“执行者”进化为“思考者”。

*   **第8步: 实现`QAAgent`与自动化质检**
    *   **任务:** 创建`QAAgent`和`AutomatedCheck` Action，对`FullDraft`进行多维度检查（术语一致性、引用格式等），生成结构化的`QAReport`。
    *   **验收标准:** `ChiefPM`的日志显示，它在审阅决策前**接收并处理**了`QAReport`的内容。

*   **第9步: 实现`TechnicalWriter`的自我反思**
    *   **任务:** 在`WriteSection` Action的`run`方法中，生成初稿后，立即调用一个内部的`_reflect`方法，使用特定Prompt让LLM对初稿打分并给出修订版。
    *   **验收标准:** 单元测试中，断言Action的最终输出是经过反思的**修订稿**，而不是初稿。

好的，这是一个非常深刻且重要的架构需求。这意味着我们不仅仅是让`TechnicalWriter`一个角色能用工具，而是要建立一个**通用的、可被任何Agent复用的MCP能力层**。同时，我们还要创建一个**专门的`ToolAgent`**，它不做其他事，只负责执行工具调用，这非常符合单一职责原则。

我将根据这个新要求，重写 `dev_order.md` 的第10步，并提出一个新的第10.5步来体现这个架构演进。

---

### **`dev_order.md` - 阶段二，第10步 & 新增第10.5步 (MCP架构演进版)**

这部分内容将替换原有的第10步，并增加一个新步骤。

---

### **阶段二：第10步: 【架构重塑】构建通用的MCP能力层**

**目标**: 将MCP客户端的交互逻辑从任何特定`Action`中解耦出来，构建一个**全局的、可被任何Agent按需访问的MCP能力层**。这标志着系统从“特定角色使用工具”演进为“任何角色都可以通过标准协议与外部世界交互”。

**理念**:
*   **能力即服务 (Capability as a Service)**: MCP工具调用能力不应被硬编码在某个`Action`中，而应作为一种类似“微服务”的基础设施存在，供团队中所有Agent按需调用。
*   **配置驱动 (Configuration-Driven)**: 一个Agent是否能使用MCP工具，以及能使用哪些工具，应该由**配置**决定，而不是由其代码实现决定，从而实现最大的灵活性。
*   **标准交互范式 (Standard Interaction Paradigm)**: 任何Agent想调用外部工具，都遵循统一的模式：生成一个特殊的`ToolCall`消息，由专门的Agent来处理。

**任务**:

1.  **创建 MCP Client 基础设施 (`metagpt_doc_writer/mcp/`)**:
    *   **`transport.py` (StdioTransport)** 和 **`client.py` (MCPClient)** 的实现保持不变（基于我们已验证的V2版本）。它们是稳定可靠的底层通信模块。

2.  **创建 `MCPManager` 作为全局服务**:
    *   **`utils/mcp_manager.py`**: `MCPManager`的职责不变，它仍然是所有`MCPClient`的管理者和工具请求的中央路由器。
    *   **实例化**: `MCPManager` 将在主流程（如`run.py`）的顶层被**实例化一次**，并作为一个**单例服务**存在。

3.  **定义标准的工具调用消息 (`schemas/doc_structures.py`)**:
    *   **新增`ToolCall`和`ToolOutput` Schema**:
        *   `ToolCall(tool_name: str, args: dict)`: 当一个LLM-Agent想要调用工具时，它不再直接执行代码，而是生成一个包含此`ToolCall`对象的`Message`。
        *   `ToolOutput(tool_name: str, output: str, is_error: bool)`: 这是工具执行后返回的结果，同样封装在`Message`中。

**验收标准**:

*   **标准1 (基础设施)**: `MCPClient`, `StdioTransport`, `MCPManager` 的单元测试通过，能成功连接到外部MCP Server并列出工具。
*   **标准2 (新Schema)**: `ToolCall` 和 `ToolOutput` 的Pydantic模型定义完成。

---

### **阶段二：第10.5步: 实现双模态工具调用与`ToolAgent`**

**目标**: 基于第10步构建的通用MCP能力层，实现两种工具调用模式：**1) 任何Agent的内部直接调用** 和 **2) 通过专门的`ToolAgent`进行委托调用**。

**任务**:

1.  **模式一：任何Agent的内部直接调用**
    *   **重构`BaseDocWriterRole`**:
        *   为其增加一个 `mcp_manager: Optional[MCPManager] = None` 属性。
        *   增加一个 `async def call_tool(self, tool_name: str, args: dict)` 的辅助方法，该方法内部直接调用`self.mcp_manager.call_tool()`。
    *   **重构`WriteSection` Action**:
        *   `run`方法现在接收`MCPManager`作为参数。
        *   其内部的MCP状态机逻辑不变，但当需要调用工具时，它直接调用`self.owner.call_tool()`（`self.owner`指向拥有该Action的Role实例）。
    *   **`TechnicalWriter`的配置**: 在初始化`TechnicalWriter`时，将全局的`MCPManager`实例注入给它。
        ```python
        # In run.py
        mcp_manager = MCPManager(...)
        await mcp_manager.start_all_servers()
        
        team.hire([
            TechnicalWriter(mcp_manager=mcp_manager),
            # ... other roles
        ])
        ```

2.  **模式二：实现专门的`ToolAgent`**
    *   **创建`metagpt_doc_writer/roles/tool_agent.py`**:
        *   这是一个**非LLM的工具人角色**。
        *   它在初始化时接收全局的 `MCPManager` 实例。
        *   它 `_watch({ToolCall})`，专门监听`ToolCall`消息。
        *   其 `_act` 方法的逻辑是：
            1.  从收到的`ToolCall`消息中解析出`tool_name`和`args`。
            2.  调用`self.mcp_manager.call_tool(tool_name, args)`。
            3.  将返回结果封装成一个`ToolOutput`消息并发布。

3.  **整合与测试**:
    *   **`test_direct_tool_call.py`**: 创建一个测试，验证`TechnicalWriter`能够成功地、直接地调用`MCPManager`执行工具。
    *   **`test_delegated_tool_call.py`**: 创建一个测试，模拟一个Agent（可以是任何Agent）发布一个`ToolCall`消息，然后验证`ToolAgent`能够接收到该消息，执行工具，并发布正确的`ToolOutput`消息。

**验收标准**:

*   **标准1 (直接调用)**: `test_direct_tool_call.py`通过。日志显示`TechnicalWriter`的`_act`方法内部成功获取了工具返回的结果。
*   **标准2 (委托调用)**: `test_delegated_tool_call.py`通过。日志显示`ToolAgent`正确地响应了`ToolCall`消息，并发布了`ToolOutput`消息。
*   **标准3 (灵活性)**: 两种模式可以共存。系统现在既支持有工具使用能力的“专家Agent”，也支持将工具调用作为一项公共服务委托给“专员Agent”。



*   **第11步: 【功能统一】为`ReviewAndCommand`实现MCP扩展**
    *   **理念:** 统一`ChiefPM`的复杂审阅逻辑与`TechnicalWriter`的工具调用逻辑，均使用MCP框架。
    *   **任务:** 重构`ReviewAndCommand`的`run`方法，构建一个包含多轮虚拟角色（如`Critic`, `Optimist`）对话的`messages`列表，再交由LLM进行最终决策。
    *   **验收标准:** 单元测试中，断言传递给`llm.acompletion`的`messages`列表长度大于3，且包含了`"name": "Critic"`等带有虚拟角色名称的条目。

---

### **阶段三：最终集成与交付 (Final Integration & Delivery)**

**目标:** 整合所有功能，完成最终交付、性能报告和项目归档。

*   **第12步: 演进`run.py`以支持完整的增强流程**
    *   **任务:** 将所有新角色和逻辑正确地串入主执行管道。
    *   **最终数据流:** `Planner` -> `GroupPM` -> `TechnicalWriter`(内含自我反思/MCP工具调用) -> `DocAssembler` -> `QAAgent` -> `ChiefPM`(审阅) -> (修订循环: `ChangeSetGenerator` -> `DocModifier` -> `DocAssembler`) -> `ChiefPM`(批准) -> `PerformanceMonitor` & `Archiver`。
    *   **验收标准 (端到端冒烟测试):**
        *   运行一个复杂任务，如：`"写一篇关于AI Agent最新进展的报告，对比MetaGPT与AutoGen，并用序列图展示其修订流程。"`
        *   **成功标准:**
            1.  程序完整运行无异常。
            2.  日志清晰展示了`TechnicalWriter`内部的MCP工具调用流程。
            3.  最终文档中**同时包含**了网络搜索内容和Mermaid图表。
            4.  日志显示修订循环**至少执行了一次**。

*   **第13步: 最终化`PerformanceMonitor`和`Archiver`**
    *   **任务:** 完善成本监控和产物归档功能。
        *   `PerformanceMonitor`: 报告应包含**总体成本**，以及**按角色、按行动细分**的Token消耗和耗时。
        *   `Archiver`: **核心是调用`team.serialize()`**，并归档所有关键产物（最终文档、过程文档、性能报告、团队快照）。
    *   **验收标准:**
        *   **标准1:** `performance_report.json`内容详尽，包含分项统计。
        *   **标准2:** `archive/`目录下的归档文件包**必须包含**最终文档、性能报告和`team_snapshot.json`。

*   **第14步: 代码清理与文档更新**
    *   **任务:** 移除所有被取代的旧角色和脚本，并更新项目的`README.md`和`ARCHITECTURE.md`，使其准确反映最终的系统设计。
    *   **验收标准:**
        *   **代码审查:** `git status`显示没有多余的、未被引用的文件。
        *   **文档审查:** `ARCHITECTURE.md`中的流程图和角色描述与本SOP最终版完全匹配。