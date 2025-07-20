

### **最终开发路线图：Artisan 项目**

**总览**: 我们将在已验证的 `hierarchical` 架构基础上，分四个核心阶段，逐步集成高级功能，包括自我优化、精细化资源调度、RAG 和高级工具（MCP）。

**项目基础**: 我们当前的 `hierarchical` 代码库，它已经实现了：
*   分层迭代的文档生成逻辑 (`ChiefPM -> Scheduler -> Executor`)。
*   基于 `Semaphore` 的并发控制。
*   基于 `config.yaml` 的深度控制。
*   内容与格式分离的最佳实践。

---

### **阶段一：引入自我优化（Review & Revise）**

**目标**: 将简单的 `Write` 工作流升级为完整的 `Write -> Review -> Revise` 循环，为系统注入基础的自我优化能力。

**要实现什么**:
1.  **创建新的 Action**:
    *   在 `hierarchical/actions/` 目录下创建 `review_section.py` 和 `revise_section.py` 文件。
    *   实现 `ReviewSection` Action：接收 `draft` 和 `context`，调用 LLM 生成结构化的评审意见（例如，一个包含`score`和`suggestions`的JSON对象）。
    *   实现 `ReviseSection` Action：接收 `draft`、`review_comments` 和 `context`，调用 LLM 生成修订后的版本。
2.  **升级 `Executor` 工作流**:
    *   在 `hierarchical/roles/executor.py` 的 `_process_section_workflow` 方法中，取消对 `Review` 和 `Revise` 调用的注释。
    *   实现完整的逻辑链：`draft = write()` -> `comments = review(draft)` -> `final_content = revise(draft, comments)`。
3.  **（可选）引入 `ActionNode`**:
    *   参考您 `Milestone 1` 的思考，可以将 `ReviewSection` 设计为一个 `ActionNode`，内部包含“评估完整性”、“评估清晰度”等子步骤，使其评审过程更结构化。

**如何验收**:
*   **AC1.1 (日志检查)**: `Executor` 的日志清晰地显示了 `WriteSection -> ReviewSection -> ReviseSection` 的完整调用顺序。
*   **AC1.2 (内容检查)**: 对比 `WriteSection` 的初稿和 `ReviseSection` 的终稿，能够看到终稿确实根据某种（模拟的或真实的）评审意见进行了优化和改进。

---

### **阶段二：实现分层LLM资源调度**

**目标**: 让系统能够根据任务类型，智能地选择不同成本和性能的 LLM，实现精细化的资源管理。我们将完全采纳您 `Milestone 2` 的设计，并将其应用到 `hierarchical` 架构上。

**要实现什么**:
1.  **配置文件分离与增强**:
    *   `/root/.metagpt/config2.yaml`: 只保留 `llm` (全局默认) 和 `models` (LLM池定义) 这两个与LLM实例相关的部分。
    *   `~/metagpt/mghier/configs/local_config.yaml` (新建): 创建一个本地配置文件，用于定义与**策略**相关的部分，例如：
        ```yaml
        # ~/metagpt/mghier/configs/local_config.yaml
        role_llm_bindings:
          ChiefPM: "strong_model"
          Scheduler: "fast_model" # Scheduler 也需要调用 LLM 了
          Executor: "fast_model"
        
        action_llm_bindings: # 更细粒度的绑定
          CreateSubOutline: "strong_model" # 规划任务用强模型
          WriteSection: "fast_model"
          ReviewSection: "strong_model" # 评审用强模型
        
        # 暂时不引入 MCP
        # mcp_servers: ...
        # role_mcp_bindings: ...
        ```
2.  **重构代码以支持动态LLM**:
    *   在 `run_hierarchical.py` 中，同时加载全局和本地的配置文件，并将本地配置（例如 `action_llm_bindings`）存入 `Context`。
    *   修改 `hierarchical/roles/` 下的**所有 `Role`**（`ChiefPM`, `Scheduler`, `Executor`）和它们调用的 **所有 `Action`**。
    *   **核心模式**: `Role` 在调用 `Action` 之前，需要根据 `action_llm_bindings` 和 `role_llm_bindings` 的配置，决定本次调用应该使用哪个 `llm_key`。然后通过 `action_instance = ActionClass(llm_name_or_type=llm_key)` 的方式动态实例化并调用 `Action`。
    *   `metagpt` 框架会自动处理从 `models` 池中查找并创建对应的 LLM 实例。

**如何验收**:
*   **AC2.1 (日志检查)**:
    *   运行系统时，`CreateSubOutline` Action 的日志显示它是由 `strong_model` 执行的。
    *   `WriteSection` Action 的日志显示它是由 `fast_model` 执行的。
    *   这证明了基于 `Action` 的 LLM 调度优先级是正确的。
*   **AC2.2 (配置灵活性)**: 修改 `local_config.yaml` 中 `WriteSection` 的绑定为 `"strong_model"`，重新运行，日志应显示 `WriteSection` 现在由 `strong_model` 执行。

---

### **阶段三：实现基于持久化路径的RAG**

**目标**: 为系统提供利用本地知识库生成内容的能力，使其不仅仅依赖LLM的通用知识。我们将采纳您 `Milestone 4` 的设计。

**要实现什么**:
1.  **创建RAG索引**:
    *   创建一个一次性脚本 `scripts/build_rag_index.py`。
    *   这个脚本负责读取一个本地目录（例如 `knowledge_base/`），并使用 `llama-index` 或类似工具，将索引文件持久化到磁盘（例如 `storage/rag_index/`）。
2.  **将索引路径注入 `Context`**:
    *   在 `run_hierarchical.py` 中，将持久化索引的路径作为一个字符串存入 `Context`，例如 `ctx.kwargs.rag_index_path = "./storage/rag_index"`。
3.  **创建 `Research` Action 并集成RAG**:
    *   在 `hierarchical/actions/` 下创建 `research.py`。
    *   `Research` Action 的 `run` 方法接收一个查询 `query`。
    *   在 `run` 方法内部，它会**即时加载 (lazy loading)** RAG 引擎：`engine = SimpleEngine.from_storage(context_path=self.context.kwargs.rag_index_path)`。
    *   然后使用 `engine.query(query)` 来检索本地知识。
4.  **在工作流中调用 `Research`**:
    *   修改 `Scheduler` 的 `_think` 逻辑。在决定为某个章节创建子大纲 (`PENDING_SUBDIVIDE`) 之前，先为其设置一个新的状态，例如 `PENDING_RESEARCH`。
    *   在 `_act` 中，当看到 `PENDING_RESEARCH` 状态时，`Scheduler` 调用 `Research` Action，并将检索到的结果存入对应 `Section` 对象的一个新字段，例如 `section.research_data: str`。然后将状态改为 `PENDING_SUBDIVIDE`。
    *   `CreateSubOutline` 和 `WriteSection` 的 Prompt 现在可以利用这个 `research_data` 来生成更具事实依据的内容。

**如何验收**:
*   **AC3.1 (准备工作)**: 在 `knowledge_base/` 目录下放入一个包含独特、非通用知识的文本文件（例如，一个虚构产品的内部技术文档）。运行 `build_rag_index.py`。
*   **AC3.2 (日志检查)**: 运行主流程时，`Scheduler` 和 `Research` Action 的日志显示它们正在为特定章节进行研究，并成功从 `storage/rag_index/` 加载了引擎。
*   **AC3.3 (内容检查)**: 最终生成的文档中，对应章节的内容**必须包含**您在本地知识库中放入的那个独特的、非通用知识点。

---

### **阶段四：集成高级工具（MCP）与最终优化**

**目标**: 将系统与 `metagpt` 生态中的高级工具（如 Model Context Protocol）集成，并解决 `tiktoken` 警告等遗留问题。

**要实现什么**:
1.  **解决 `tiktoken` 警告**:
    *   研究 `metagpt` 的 `TokenCounter` 或相关文档，找到为非 OpenAI 模型（如 `mistral-medium-latest`）注册自定义 token 计算函数的方法，或者选择一个 `tiktoken` 支持的相近编码作为近似值。
2.  **集成 MCP**:
    *   在 `local_config.yaml` 中，恢复 `mcp_servers` 和 `role_mcp_bindings` 的配置。
    *   在 `run_hierarchical.py` 中，初始化 `MCPManager` 并启动服务。
    *   创建一个新的 `Action`，例如 `GenerateDiagram`，它的 `run` 方法会调用 `self.context.mcp_manager.call_tool("diagram_generator", ...)`。
    *   修改 `Scheduler` 的逻辑，使其能够在适当的时候（例如，LLM在内容中生成了一个特定标记 `[GENERATE_DIAGRAM: ...]`）触发这个 `GenerateDiagram` Action。
3.  **错误处理与重试**:
    *   使用 `tenacity` 库为所有与外部服务（LLM, MCP, RAG）交互的 `Action` 的 `run` 方法添加 `@retry` 装饰器，使系统在面对临时网络波动时能自动重试。

**如何验收**:
*   **AC4.1 (日志检查)**: 运行系统时，不再出现 `tiktoken` 相关的 `Warning`。
*   **AC4.2 (MCP功能检查)**: 在 `local_config.yaml` 中配置一个模拟的 MCP 服务器。运行系统时，日志显示 `MCPManager` 成功启动，并且在特定条件下，`GenerateDiagram` Action 被调用，并成功与模拟服务器通信。
*   **AC4.3 (健壮性测试)**: （需要手动修改代码）暂时让某个 `Action` 的 LLM 调用第一次必定失败。运行系统，日志应显示 `tenacity` 的重试日志，并且 `Action` 在第二次尝试时成功。

---
