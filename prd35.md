## metagpt文档撰写多智能体prd v3.5

  
  

### **1.0 核心设计理念 (Core Design Philosophy)**

  

本SOP旨在构建一个**自进化 (Self-Evolving)、高鲁棒性 (Highly Robust)、可度量 (Measurable)** 的自主文档生成系统。它不仅继承了成熟的、模仿人类专业团队的协作流程，更在关键技术模块上进行了深度优化和创新，使系统从一个“被动执行指令的工厂”升级为一个“能够主动思考、自我优化和利用外部工具的智能有机体”。

  

*   **1.1. 分层级、专业化的协作架构 (Hierarchical, Specialized Collaboration Architecture)**

    *   **理念**: 任何复杂的智力劳动都可以通过模拟现实世界中的高效组织来完成。我们将文档创作这一复杂任务解构为战略规划、战术执行和工具操作三个明确的层次。

    *   **实现**:

        *   **决策层 (Strategy Layer)**: 如`ChiefPM`和`GroupPM`，使用顶级推理模型，负责“做什么”（What）的顶层设计、需求拆解和最终决策，确保方向的正确性。

        *   **执行层 (Execution Layer)**: 如`TechnicalWriter`，负责“怎么做”（How）的具体内容生成。此层级可根据任务复杂性配置不同成本效益的模型，实现资源优化。

        *   **工具层 (Tooling Layer)**: 如`DocModifier`和`DocAssembler`，作为非LLM的确定性Agent，负责精确、无歧义的任务，保证了大规模操作的稳定性和可预测性。

  

*   **1.2. 『准结构化』指令驱动的增量式修订 (Quasi-structured Instruction-driven Incremental Revision)**

    *   **理念**: 让LLM直接编辑长文本或生成精确的、基于行号的修改指令是不可靠且脆弱的。我们必须将“语义审阅”、“指令转换”和“编辑执行”分解为独立、解耦的步骤，以实现鲁棒的长文本修订。

    *   **实现**:

        *   **1.2.1. 两阶段指令生成 (`Two-Phase Command Generation`)**:

            1.  **语义决策**: `ChiefPM`审阅后，输出一份**自然语言**的审阅笔记（`ReviewNotes`），专注于高质量的内容评审与修改意图的表达。

            2.  **指令转换与验证**: 引入一个新的**`ChangeSetGenerator`**角色，专门负责将`ChiefPM`的自然语言笔记，转换为基于**上下文锚点 (Context Anchors)** 的、结构化的`ChangeSet` JSON。此过程包含**验证-修复循环**，确保最终指令的语法和逻辑100%正确，可被机器安全执行。

        *   **1.2.2. 上下文锚点 (`Context Anchors`)**: 修订指令不再依赖易变的“绝对行号”，而是使用文档中唯一的文本片段作为“锚点”进行定位（例如，“在‘核心设计理念’这一段后面插入...”）。这使得指令即使在文档内容发生小幅变动后依然有效，极大提升了鲁棒性。

        *   **1.2.3. 精确执行 (`Precise Execution`)**: `DocModifier`（工具人Agent）接收经过验证的`ChangeSet`，通过纯代码逻辑精确地执行修改，保证了大规模修订的原子性、精确性和完全可追溯性。

  

*   **1.3. 双模态上下文管理 (Dual-Modal Context Management)**

    *   **理念**: 系统的上下文分为两种截然不同的类型：**静态长文档**和**动态对话历史**。必须采用不同的、最优化的技术来处理，以兼顾效率和质量。

    *   **实现**:

        *   **1.3.1. 针对静态长文档的『临时RAG』压缩 (`Ephemeral RAG for Static Documents`)**:

            *   **场景**: 当Agent需要处理一个完整的、一次性的长文本时（如`ChiefPM`审阅整个`FullDraft`）。

            *   **技术**: 调用`ContextOptimizer`模块。该模块在检测到上下文溢出时，会**即时地、在内存中**为该文档构建一个临时RAG索引，并使用任务指令作为查询，快速检索出最相关的段落，形成一个压缩后的、语义丰富的上下文。

            *   **价值**: 避免了对API的暴力截断，保证了长文档处理任务的质量和连贯性。

        *   **1.3.2. 针对动态对话历史的『增量RAG』管理 (`Incremental RAG for Dynamic Conversations`)**:

            *   **场景**: 当Agent需要长期记忆，并回顾其与其他Agent的多轮交互历史时。

            *   **技术**: 为需要长期记忆的Agent配备一个内部的`ConversationManager`组件。该组件持有一个**有状态、持久化**的RAG索引。每当有新消息产生，它会**增量地**将该消息加入索引，而无需重新处理整个历史。当需要回顾时，Agent向该管理器发起查询，高效检索出相关的历史记忆。

            *   **价值**: 实现了高效、可扩展的长期记忆机制，避免了重复处理历史记录带来的性能瓶颈，使Agent能够进行更复杂的、基于长期上下文的推理。

  

*   **1.4. 从“被动执行”到“主动智能” (From "Passive Execution" to "Proactive Intelligence")**

    *   **理念**: 顶级的Agent不应仅仅是指令的接收者，而应具备一定程度的自主性，包括自我审视、动态规划和利用外部世界知识的能力。

    *   **实现**:

        *   **1.4.1. 行动后反思与自我修正 (`Post-Action Reflection & Self-Correction`)**:

            *   **机制**: 核心内容生成`Action`在产出初稿后，会触发一个内部的`_reflect`私有方法。此方法使用一个特定的“反思Prompt”，对输出进行多维度自我评估，并根据评估结果进行第二轮优化。

            *   **价值**: 显著提高了单次任务的“首轮通过率”，减轻了后续人工审阅的压力，并减少了整体的修订循环次数。

        *   **1.4.2. 动态工具调用与多模态扩展 (`Dynamic Tool-use & Multi-modal Expansion`)**:

            *   **机制**: 关键Agent被赋予一个`ToolRegistry`（工具注册表）。在执行任务时，LLM可以自主判断是否需要调用某个工具（如`Web_Search`, `Diagram_Generator`），并在输出中生成特殊的`[TOOL_CALL]`指令，由框架解析并执行。

            *   **价值**: 极大扩展了Agent的能力边界，使其能处理需要外部实时信息、代码执行或图表生成等复杂任务，使文档内容更丰富、更具时效性。

        *   **1.4.3. 全面的质量保障与成本控制 (`Holistic QA & Cost Control`)**:

            *   **机制**: 引入专门的`QAAgent`在人工审阅前进行自动化质检，以及一个非LLM的`PerformanceMonitor`角色，静默记录全流程的性能数据（Token消耗、成本、耗时）。

            *   **价值**: 建立了体系化的质量与效率度量衡。QA流程前置化降低了昂贵的修订成本，而性能监控则为SOP的持续优化提供了精确的数据支持。

  
  

### **2.0 团队角色与职责 (Team Roles & Responsibilities)**

  

团队由决策、执行与精炼、质量、增强与指令化、工具四个层次的Agent构成，各司其职，通过MetaGPT的`Environment`和`Message`机制进行高效协作。每个角色的设计都与其在SOP中的特定任务和所需的核心能力紧密耦合。

  

*   **2.1. 决策层 (Strategy Layer)**

    *   **2.1.1. `ChiefPM` (产品总监)**

        *   **职责**:

            1.  **顶级规划**: 接收初始用户需求，进行最高层次的主题拆解，输出`ProjectPlan`消息。

            2.  **任务审批**: 审批由`TaskRefiner`精炼后的任务（`RefinedTask`），确保每个任务清晰、可执行，输出`ApprovedTask`消息。

            3.  **最终审阅与决策**:

                *   审阅`DocAssembler`整合的完整草稿（`FullDraft`），并结合`QAAgent`的报告。

                *   若需修改，输出一份**自然语言格式的审阅笔记（`ReviewNotes`）**消息，交由`ChangeSetGenerator`处理。

                *   若文档完善，发布最终的**`Approval`**消息，以终止修订循环并启动交付流程。

        *   **核心能力**: 强大的逻辑推理与规划能力；**使用`ContextOptimizer`处理长文档**；动态RAG决策；高质量的语义审阅与意见表达。

        *   **配置**: 必须使用顶级推理LLM (e.g., GPT-4o, Claude 3 Opus)。

  

    *   **2.1.2. `GroupPM` (模块产品经理)**

        *   **职责**: 接收`ProjectPlan`中的模块标题，将其细化为包含章节和子章节的详细大纲（`ModuleOutline`）。

        *   **核心能力**: **探索式RAG**（主动查询知识库以丰富大纲内容）；生成包含`rag_hint`的结构化大纲，为下游`TechnicalWriter`提供知识检索线索。

        *   **配置**: 强推理LLM (e.g., GPT-4o)。

  

*   **2.2. 执行与精炼层 (Execution & Refinement Layer)**

    *   **2.2.1. `TaskDispatcher` (任务派发员)**

        *   **职责**: 将`ModuleOutline`中的每个章节标题快速转化为初步的任务描述（`InitialTask`）。这是一个批量、快速的转换过程。

        *   **核心能力**: 快速的语言格式转换，不要求深度思考。

        *   **配置**: 快速、经济的LLM (e.g., GPT-3.5-Turbo, Llama3-8B)。

  

    *   **2.2.2. `TaskRefiner` (任务精炼师)**

        *   **职责**: 接收`InitialTask`，利用CoT（思维链）对其进行丰富和细化，补充背景、关键点和验收标准，输出高质量的`RefinedTask`。

        *   **核心能力**: 思维链推理；任务细节与上下文补充。

        *   **配置**: 强推理LLM (e.g., GPT-4o)。

  

    *   **2.2.3. `TechnicalWriter` (技术写手)**

        *   **职责**: 根据`ApprovedTask`撰写具体的章节内容，输出`DraftSection`消息。这是内容创作的核心执行者。

        *   **核心能力**:

            *   **动态RAG决策**: 自主判断是否需要查询知识库。

            *   **动态工具调用**: 根据需要调用`Web_Search`或`Diagram_Generator`等工具。

            *   **行动后反思修正**: 完成初稿后进行内部审视和迭代优化。

            *   **（可选）增量RAG记忆**: 若任务需要跨多轮交互的记忆，则利用内部的`ConversationManager`进行高效的上下文回顾。

        *   **配置**: 性能与成本均衡的LLM (e.g., GPT-4o-mini, Gemini 1.5 Pro)。

  
#### **2.3. 质量、增强与指令化层 (Quality, Enhancement & Instruction-lization Layer)**

此层级的Agent专注于提升内容的质量、扩展Agent的能力，并确保人类或高阶Agent的意图能够被精确地转换为机器可执行的指令。

*   **2.3.1. `QAAgent` (质量保证工程师)**
    *   **职责**: 在`ChiefPM`审阅前，对`FullDiagram`进行自动化多维度质检，并生成`QAReport`消息。
    *   **核心能力**: 事实一致性校验（对比RAG源）、关键术语检查、遵循风格指南（Style Guide）检查、格式规范性检查。
    *   **配置**: 强推理LLM (e.g., GPT-4o)。

*   **2.3.2. `ChangeSetGenerator` (指令生成器)**
    *   **职责**: 接收`ChiefPM`的自然语言`ReviewNotes`和`FullDraft`，将其转换为结构化的、基于上下文锚点的`ChangeSet` JSON。这是保障修订流程鲁棒性的关键角色。
    *   **核心能力**: 精确的指令转换能力；内置**语法验证和逻辑验证的修复循环**，确保输出的`ChangeSet`100%可被机器执行。
    *   **配置**: 强推理LLM，需要具备优秀的遵循指令和格式生成能力 (e.g., GPT-4o)。

*   **2.3.3. `DiagramGenerator` (图表生成器 - 工具人)**
    *   **职责**: 作为一个被`TechnicalWriter`调用的工具，接收自然语言指令，生成图表的代码（如Mermaid.js）。
    *   **核心能力**: 解析指令，生成特定领域语言（DSL）的代码。
    *   **配置**: 可为专用微调模型，或带有特定系统Prompt的通用LLM。**在MetaGPT框架下，它通常被实现为一个独立的`Action`，该`Action`不依赖`Role`的`_think`决策，而是直接被其他`Action`（如`TechnicalWriter`的`WriteSection`）通过工具API的方式调用。**

#### **2.4. 工具层 (Tooling Layer)**

工具层的Agent是确定性的、非LLM的角色。它们负责执行精确、无歧义的任务，保证了大规模操作的稳定性和可预测性。

*   **2.4.1. `DocAssembler` (文档组装工 - 非LLM)**
    *   **职责**:
        1.  **组装草稿**: 收集所有`DraftSection`和`DiagramSection`，按顺序组装成`FullDraft`。为了支持上下文锚点，它需要为每个段落或重要块添加唯一的、可定位的标记。
        2.  **最终定稿**: 接收到`Approval`指令后，移除所有内部标记（如行号、锚点ID），清理格式，生成最终交付的`final_document.md`文件。
    *   **配置**: **非LLM，纯Python代码。** 在实现上，它是一个继承自 `metagpt.Role` 的类，但其 `set_actions` 为空，其行为完全由 `_act` 方法中的确定性代码逻辑驱动。

*   **2.4.2. `DocModifier` (文档修改工 - 非LLM)**
    *   **职责**: 精确执行`ChangeSetGenerator`生成的、经过验证的`ChangeSet`指令，对`FullDraft`进行修改，并输出一个新版本的`FullDraft`消息。
    *   **配置**: **非LLM，纯Python代码。** 在实现上，它是一个继承自 `metagpt.Role` 的类，但其 `set_actions` 为空，其行为完全由 `_act` 方法中的确定性代码逻辑驱动。

*   **2.4.3. `PerformanceMonitor` (性能监视器 - 非LLM)**
    *   **职责**: 作为环境中的“幽灵观察者”，通过订阅`Environment`中的所有消息，静默记录每个`Action`的Token消耗、API调用耗时、预估成本等元数据。在流程结束时，生成一份完整的性能报告。
    *   **配置**: **非LLM，纯Python代码。** 在实现上，它是一个继承自 `metagg.Role` 的类，但其 `set_actions` 为空，其行为完全由 `_act` 方法中的确定性代码逻辑驱动。

*   **2.4.4. `Archiver` (项目归档员 - 新增非LLM工具人)**
    *   **职责**: 在项目最终批准后，负责收集所有关键产物（最终文档、过程文档、性能报告），并创建项目状态快照，为未来的审计和增量开发做准备。
    *   **核心能力**: 文件I/O操作；**调用MetaGPT的`team.serialize()`方法**；（可选）与版本控制系统（如Git）交互。
    *   **配置**: **非LLM，纯Python代码。** 在实现上，它是一个继承自 `metagpt.Role` 的类，但其 `set_actions` 为空，其行为完全由 `_act` 方法中的确定性代码逻辑驱动。
  
  

### **3.0 关键技术模块详解 (Key Technology Modules)**

  

本节将深入剖析支撑SOP V3.2高效、智能、稳定运行的三大核心技术模块。这些模块不仅是理论上的设计，更是基于MetaGPT框架特性（如`Role`, `Action`, `RAG Engine`）的具体实现方案。

  

#### **3.1. 双模态上下文管理 (Dual-Modal Context Management)**

  

**理念**: 系统的上下文分为两种截然不同的类型：**静态长文档**（如一篇完整的草稿）和**动态对话历史**（如Agent间的连续交互）。必须采用不同的、最优化的技术来处理这两种上下文，以兼顾效率和质量。



 **3.1.1. 针对静态长文档的『临时RAG』压缩 (`ContextOptimizer`)**

*   **理念 (Philosophy)**
    系统的上下文分为两种截然不同的类型：**静态长文档**（如一篇完整的草稿）和**动态对话历史**（如Agent间的连续交互）。必须采用不同的、最优化的技术来处理这两种上下文，以兼顾效率和质量。`ContextOptimizer`模块正是为高效、智能地处理静态长文档而生。

*   **应用场景 (Application Scenario)**
    当Agent需要处理一个完整的、一次性的长文本时。最典型的场景是`ChiefPM`在`ReviewAndCommand`行动中审阅整个`FullDraft`，或者`TechnicalWriter`在撰写前需要整合大量的背景资料。

*   **实现机制 (Implementation Mechanism)**
    1.  **定义**: 创建一个可复用的`ContextOptimizer`类，其核心是一个静态异步方法 `process(context: str, instruction: str, llm, max_tokens: int) -> str`。
    2.  **触发时机**: 在`Action`的`run`方法内部，调用`self._aask()`之前，先调用此优化器对潜在的长上下文进行预处理。
    3.  **核心算法**:
        *   **前置检查**: 首先计算组合后的总Token数，若未超出`max_tokens`限制，则直接返回原始上下文，避免不必要的计算。
        *   **即时压缩**: 如果检测到溢出，模块会**即时地、在内存中**为该长文本`context`构建一个临时的RAG索引（使用`SimpleEngine.from_texts()`）。然后，它将任务指令`instruction`作为查询，从临时索引中检索出最相关的段落，并重组为一个压缩后的、语义丰富的上下文，确保其长度在`max_tokens`范围内。

*   **风险与考量 (Risks & Considerations)**
    *   **性能与资源瓶颈**: 对于极端巨大的文档（例如，超过10MB的文本），即时在内存中构建RAG索引可能会消耗大量内存并导致显著的运行时延迟。
    *   **应对策略**: 因此，`ContextOptimizer`内部应设置一个合理的输入大小阈值（例如，10MB）。当输入超过该阈值时，模块不应尝试处理，而是应抛出一个警告或特定的异常，并引导用户将此大型文档作为预构建知识库的一部分进行离线处理，以保证系统的响应速度和稳定性。

*   **价值 (Value)**
    彻底解决了长文本输入的溢出问题。通过保留最相关信息而非暴力截断，极大地保证了长文本处理任务（如审阅、总结）的质量和连贯性，使Agent的决策基于更全面的信息。



  

*   **3.1.2. 针对动态对话历史的『增量RAG』管理 (`ConversationManager`)**

    *   **应用场景**: 当Agent需要长期记忆，并回顾其与其他Agent的多轮交互历史以做出决策时。

    *   **实现机制**:

        1.  **定义**: 为需要长期记忆的`Role`引入一个内部的`ConversationManager`组件，该组件在`Role`初始化时创建，并持有一个**有状态、持久化**的RAG引擎实例。

        2.  **增量添加**: 每当有新消息产生（例如在`_observe`或`_act`之后），就调用`self.conversation_manager.add_message(message)`，该方法会将新消息的文本**增量地**加入到内部的RAG索引中，而无需重新处理整个历史。

        3.  **高效检索**: 当Agent需要回顾历史时，它不再是获取最后`k`条消息，而是向`ConversationManager`发起一个与当前任务相关的查询（如`retrieve("总结一下关于第二章的所有反馈")`），从而高效地获取最相关的历史记忆片段。

    *   **价值**: 实现了高效、可扩展的长期记忆机制。它避免了在处理序列化任务时对历史记录的重复计算，使Agent能够进行更复杂的、基于长期上下文的推理，同时保持高性能。

  

#### **3.2. 知识检索 (Knowledge Retrieval)**

  

*   **3.2.1. 预构建持久化索引 (Pre-built Persistent Index)**

    *   **理念**: 对于大型、不频繁变动的知识库，采用“一次构建，多次使用”的策略以最大化效率。

    *   **实现机制**:

        1.  **离线构建**: 通过独立脚本（如`build_index.py`），使用`metagpt.rag.engines.SimpleEngine.from_docs()`加载所有参考文档，并调用`.persist()`方法将索引持久化到磁盘。

        2.  **在线加载**: 在主流程中，需要RAG的`Action`通过`SimpleEngine.from_index()`快速从磁盘加载预构建好的索引，实现近乎瞬时的RAG能力启动。

  

*   **3.2.2. Agent自主RAG决策 (Agent-driven RAG Decision)**

    *   **理念**: 专家会自主判断何时需要查阅资料。我们的Agent也应具备此能力，以节省成本并避免不必要的信息干扰。

    *   **实现机制**: 在`TechnicalWriter`或`ChiefPM`的核心`Action`内部，增加一个前置的、轻量级的LLM决策步骤，通过一个简单的Prompt（例如，“为了完成任务`{task}`，你是否必须查阅知识库？请只回答'YES'或'NO'。”）来决定是否执行后续的RAG查询。

  

*   **3.2.3. 多策略RAG查询 (Multi-Strategy RAG Query)**

    *   **理念**: 不同的问题类型适合不同的检索策略。Agent应能根据问题选择最优的检索组合。

    *   **实现机制**: MetaGPT的RAG模块支持混合检索（如`FAISSRetrieverConfig` + `BM25RetrieverConfig`）。`Action`中的决策逻辑可以升级，让LLM判断任务是“概念理解型”（使用向量检索）、“关键词查找型”（使用BM25）还是“综合型”（使用混合检索），从而动态构建`retriever_configs`列表。

  

#### **3.3. Agent智能与可靠性增强 (Agent Intelligence & Reliability Enhancement)**

  

*   **3.3.1. 行动后反思模块 (Post-Action Reflection Module)**

    *   **理念**: 一次性完美输出是困难的。引入一个即时的自我审视和修正循环，可以显著提高单次`Action`交付的质量。

    *   **实现机制**: 在`TechnicalWriter`等关键内容生成`Action`的`run`方法中，在生成初稿后，调用一个内部的`_reflect(request, output)`方法。该方法会使用一个特定的“反思Prompt”要求LLM对输出进行多维度评估（如完整性、清晰度），并根据评估结果生成一个改进版本。

  

*   **3.3.2. 动态工具箱 (Dynamic Toolbox)**

    *   **理念**: 将Agent的能力从纯文本生成扩展到与外部世界互动、执行代码或生成多模态内容。

    *   **实现机制**: 为`TechnicalWriter`等`Role`提供一个`ToolRegistry`（工具注册表）。在其主Prompt中告知可用工具及其调用格式（如`[TOOL_CALL: DiagramGenerator(...)]`）。`Role`的`_act`方法在收到LLM响应后，会检查并解析`TOOL_CALL`指令，调用相应工具，并将结果作为上下文进行下一步生成。

  
 *   **3.3.3. 验证-修复式指令生成 (`Validated & Repaired Instruction Generation`)**

*   **理念 (Philosophy)**
    这是为了解决让LLM直接生成精确结构化`ChangeSet`的脆弱性问题而设计的核心模块，是整个修订流程**鲁棒性的基石**。它承认LLM在生成严格格式化数据时可能出现的错误，并通过一个自动化的验证和修复流程来确保最终输出的绝对可靠。

*   **实现机制 (Implementation Mechanism)**
    这是一个由`ChangeSetGenerator`角色执行的、包含**验证-修复循环 (Validation-Repair Loop)** 的流程：
    1.  **指令转换尝试**: `ChangeSetGenerator`接收`ChiefPM`的自然语言`ReviewNotes`，其核心`Action`要求LLM将其转换为基于上下文锚点的`ChangeSet` JSON。
    2.  **语法验证 (Syntactic Validation)**: `Action`的Python代码接收LLM的输出后，立刻执行`json.loads()`。
        *   **失败？-> 启动修复**: 如果解析失败，捕获异常。然后，将原始的错误信息和格式错误的JSON字符串一起作为新的上下文，再次请求LLM，并使用一个专门的修复Prompt：“请修复以下JSON的格式错误：...”。此循环可重试2-3次，直到JSON语法正确为止。
    3.  **逻辑验证与锚点增强 (Logical Validation & Anchor Enhancement)**: JSON格式正确后，代码遍历`ChangeSet`中的每条指令，进行逻辑上的“空运行”（Dry Run）。
        *   **锚点策略**: 为提高锚点的唯一性、稳定性和可调试性，`DocAssembler`在生成锚点时，应使用**文本内容的哈希值**来生成唯一的锚点ID，例如 `f"anchor-id::{hashlib.sha1(anchor_text.encode()).hexdigest()[:12]}"`。
        *   **验证过程**: 逻辑验证步骤将优先使用这个唯一的`anchor-id`在`FullDraft`中进行查找。
        *   **失败？-> 启动修复**: 如果某个`anchor-id`在文档中找不到，说明LLM幻觉出了错误的定位信息。此时，将此情况反馈给LLM，Prompt为：“你提供的锚点ID `{anchor-id}` 在文档中未找到，请仔细阅读上下文，重新为这条修改意见 `{review_note}` 生成正确的定位和指令”。
    4.  **安全输出**: 只有通过了**语法和逻辑双重验证**的`ChangeSet`，才会被封装为`ValidatedChangeSet`消息，发送给`DocModifier`执行。

*   **价值 (Value)**
    该机制确保了无论LLM的输出多么不稳定，最终传递给确定性执行单元`DocModifier`的指令都是100%格式正确且逻辑上可执行的。这极大地提升了整个多智能体系统的稳定性和可靠性，避免了因LLM的随机性而导致的流程崩溃。

  
  
  

### **4.0 标准作业流程 (SOP) - 分阶段详述**

  

本流程将复杂的文档生成任务分解为五个明确的阶段：环境配置、规划与任务化、内容生成、修订与审批、最终交付。每个阶段由特定的Agent角色驱动，并通过MetaGPT的`Environment`和`Message`机制无缝衔接。

  

#### **阶段零：环境与配置 (Environment & Configuration)**

  

在任何Agent开始工作前，必须先准备好运行环境和所需资源。

  

1.  **全局配置文件 (`config2.yaml`)**:

    *   **LLM配置**: 定义全局默认的`api_type`, `model`, `api_key`, `base_url`等。

    *   **RAG配置**: 配置`embedding`模型（如`openai`, `azure`, `ollama`）及其`dimensions`。

    *   **工具配置**: 配置外部工具的API密钥，如`search`（用于Web搜索）、`azure_tts`等。

    *   **人工介入 (`human_in_loop`)**: 保持为 `true`，允许在关键决策点（如`ChiefPM`审阅）进行人工干预。

  

2.  **角色级资源配置**:

    *   在主流程脚本中，实例化不同性能的`LLM`对象，并在`Team.hire()`时注入给不同的`Role`。

    *   **示例**:

        ```python

        from metagpt.provider import OpenAI

        llm_strategy = OpenAI(model="gpt-4o") # 用于决策层

        llm_execution = OpenAI(model="gpt-4o-mini") # 用于执行层

        llm_fast = OpenAI(model="gpt-3.5-turbo") # 用于快速转换任务

        team.hire([

            ChiefPM(llm=llm_strategy),

            GroupPM(llm=llm_strategy),

            TaskRefiner(llm=llm_strategy),

            TaskDispatcher(llm=llm_fast),

            TechnicalWriter(llm=llm_execution)

            # ...

        ])

        ```

  

3.  **RAG知识库构建**:

    *   运行独立的`build_index.py`脚本，使用`metagpt.rag.engines.SimpleEngine.from_docs()`加载所有参考文档，并通过`.persist()`将其构建成一个持久化的向量索引。这是**预构建持久化索引**策略的体现。

  

4.  **并发与性能监控**:

    *   在主流程中初始化`asyncio.Semaphore`，用于后续并行任务的并发控制。

    *   初始化`PerformanceMonitor`并将其加入`Team`，让它开始监听所有事件。

  

#### **阶段一：分层级大纲规划 (Hierarchical Outline Planning)**

  

**目标**: 将模糊的用户需求转化为结构清晰、可执行的大纲。

  

*   **步骤 1: 项目启动与顶级规划**

    *   **角色**: `ChiefPM`

    *   **核心行动**: `DecomposeTopic`

    *   **输入**: 初始用户需求 `Message`。

    *   **上下文策略**: 直接输入。此阶段不使用RAG，进行纯粹的高层逻辑拆分。

    *   **输出**: `ProjectPlan`消息，包含文档的顶级模块列表，如 `{"modules": ["I. 基础概念篇", "II. 实践操作篇"]}`。

  

*   **步骤 2: 模块细化与RAG增强**

    *   **角色**: `GroupPM`

    *   **核心行动**: `CreateModuleOutline`

    *   **输入**: `ProjectPlan`中的单个模块标题。

    *   **上下文策略 (探索式RAG)**:

        1.  行动首先使用模块标题对预构建的RAG知识库进行`aquery()`。

        2.  将检索到的信息摘要注入到Prompt中，要求LLM生成包含详细章节和`rag_hint`（为下游`TechnicalWriter`提供的检索线索）的`ModuleOutline` JSON。

    *   **输出**: 多个`ModuleOutline`消息，每个对应一个模块。

    *   **执行方式**: `Team`环境会将多个模块任务并行分发给多个`GroupPM`实例（或一个`GroupPM`实例处理多次）。使用`asyncio.Semaphore`和`asyncio.gather`控制并发，防止API速率超限。

  

#### **阶段二：结构化任务分配与精炼 (Structured Task Assignment & Refinement)**

  

**目标**: 将大纲中的每个章节转化为一个具体、详尽、可供`TechnicalWriter`直接执行的任务。

  

*   **步骤 3-5: 任务派发 -> 精炼 -> 审批流水线**

    *   这是一个由三个Agent紧密协作的异步流水线，并行处理所有章节。

    *   **`TaskDispatcher` -> `GenerateInitialTask`**:

        *   **输入**: `ModuleOutline`中的一个章节条目。

        *   **上下文策略**: 直接输入，使用快速LLM。

        *   **输出**: `InitialTask`消息（初步的任务描述）。

    *   **`TaskRefiner` -> `RefineTask`**:

        *   **输入**: `InitialTask`消息。

        *   **上下文策略**: 直接输入，但使用CoT（思维链）Prompt和强LLM，丰富任务细节。

        *   **输出**: `RefinedTask`消息。

    *   **`ChiefPM` -> `ApproveTask`**:

        *   **输入**: `RefinedTask`消息。

        *   **上下文策略**: 非LLM，纯代码逻辑，可设计为自动批准或根据规则筛选。

        *   **输出**: `ApprovedTask`消息，标志着该任务已准备好被撰写。

  

#### **阶段三：(增强的) 内容生成与自我修正 (Enhanced Content Generation & Self-Correction)**

  

**目标**: 高质量地完成每个章节的撰写。

  

*   **步骤 6: `TechnicalWriter` -> `WriteSection` (核心增强步骤)**

    *   **输入**: `ApprovedTask`消息。

    *   **上下文策略与执行流程**:

        1.  **工具使用决策**: 首先判断任务是否需要RAG之外的工具（如图表）。若需要，可生成对`DiagramGenerator`的子任务指令。

        2.  **自主RAG决策**: 判断是否需要查询RAG知识库。若需要，则执行`aquery()`。

        3.  **组合与优化上下文**: 将任务描述、RAG结果、工具调用结果（如有）等组合成一个长上下文。

        4.  **调用`ContextOptimizer`**: 对上述组合后的上下文进行智能压缩，确保不溢出。这是**临时RAG压缩**的应用。

        5.  **内容初稿生成**: 调用LLM生成草稿。

        6.  **自我反思与修正**: 调用内部的`_reflect`方法，对草稿进行一轮自我迭代优化。

    *   **输出**: `DraftSection`消息（包含章节ID和优化后的内容）。

  
  
  

### **阶段四：(鲁棒的) 组装、审核与修订循环 (Robust Assembly, Review & Revision Cycle) - 详细展开版**

  

**核心目标**: 将分散的章节草稿（`DraftSection`）高效、可靠地整合、审阅并迭代修订，直至达到`ChiefPM`的最终批准标准。此阶段是整个SOP的质量控制中枢，其设计的鲁棒性直接决定了最终产物的质量和生成过程的稳定性。

  

---

  

#### **步骤 7: 全文档组装 (`DocAssembler`)**

  

*   **角色**: `DocAssembler` (非LLM工具人)

*   **触发**: `DocAssembler`通过`_watch`机制，监听并等待收集到所有预期的`DraftSection`消息。`Team`环境或主控逻辑需要负责判断所有`TechnicalWriter`的任务是否已完成。

*   **核心行动**: `AssembleDocument`

*   **输入**:

    1.  一个`list[DraftSection]`，包含所有章节的内容和元数据（如章节ID）。

*   **内部逻辑**:

    1.  **排序**: 根据`DraftSection`的章节ID对列表进行精确排序，确保文档结构正确。

    2.  **内容拼接**: 遍历排序后的列表，将所有章节内容拼接成一个单一的字符串。

    3.  **注入锚点**: 这是**关键步骤**。在拼接过程中，为每个有意义的文本块（如段落、标题、列表项）添加一个唯一的、可被程序解析的上下文锚点标记。

        *   **锚点格式**: `[anchor-id::{uuid.uuid4()}]`。这个标记对LLM不可见（或通过Prompt指示其忽略），但可被`DocModifier`用于精确定位。

        *   **示例输出**:

            ```markdown

            [anchor-id::a1b2c3d4]

            # 1. 核心设计理念

  

            [anchor-id::e5f6g7h8]

            本SOP旨在构建一个...

  

            [anchor-id::i9j0k1l2]

            它不仅继承了...

            ```

*   **输出**: 一个`FullDraft`消息。其`content`字段包含带锚点的完整文稿，同时`metadata`字段可能包含一个锚点ID到原始文本的映射表，供`ChangeSetGenerator`查询。

  

---

  

#### **步骤 8: 自动化质量检查 (`QAAgent`) (可选但推荐)**

  

*   **角色**: `QAAgent` (LLM Agent)

*   **触发**: `_watch([FullDraft])` - 监听到新的完整草稿后自动启动。

*   **核心行动**: `AutomatedCheck`

*   **输入**: `FullDraft`消息。

*   **内部逻辑**:

    1.  **多维度检查**: 并行或串行执行多个检查任务。

        *   **事实核查**: 如果草稿内容大量基于RAG，可将相关部分与源材料进行对比，检查是否存在不一致。

        *   **风格指南检查**: 根据预设的风格指南（如“语气应专业”、“避免使用第一人称”），让LLM评估文档的遵循度。

        *   **术语一致性**: 提取文档中的关键术语，检查其使用是否前后一致。

    2.  **报告生成**: 将所有检查发现的问题和建议汇总成一个结构化的报告。

*   **输出**: 一个`QAReport`消息。


#### **步骤 9: 总监审阅与意图表达 (`ChiefPM`)**

*   **角色**: `ChiefPM` (LLM Agent)
*   **触发**: `_watch([FullDraft, QAReport])` - 同时接收到草稿和QA报告后启动（如果`QAAgent`被启用）。
*   **核心行动**: `ReviewAndCommand`
*   **输入**:
    1.  `FullDraft`消息。
    2.  `QAReport`消息（可选）。
*   **内部逻辑 (Internal Logic)**:
    1.  **上下文准备**:
        *   **调用`ContextOptimizer`**: `FullDraft`内容很长，行动首先调用`ContextOptimizer`，使用`"请总结并突出这份文档中的关键部分和潜在问题"`作为`instruction`，对全文进行智能压缩，得到一个可供LLM高效处理的“审阅摘要”。
        *   **Prompt构建**: 将“审阅摘要”、`QAReport`（如果有）和原始用户需求组合成最终的审阅Prompt。
    2.  **LLM决策**: LLM根据丰富的上下文，做出决策。
        *   如果认为文档已完善，则生成一个“批准”的意图。
        *   如果需要修改，则生成详细的、**自然语言的**修改意见列表。
    3.  **[风险与补充] 熔断机制 (Circuit Breaker)**:
        *   **`ChiefPM`角色内部维持一个修订计数器。每次执行`ReviewAndCommand`行动时，计数器加一。当计数器达到预设的`MAX_REVISIONS`（例如5次）时，即使仍有不满意之处，也应强制输出`Approval`消息，并在最终报告中标记此事项，以防止流程陷入死循环。**
*   **输出**:
    *   **情况一 (需修改)**: 一个`ReviewNotes`消息，`content`字段是Markdown格式的审阅笔记。
    *   **情况二 (已完善)**: 一个`Approval`消息。 **此消息将终止修订循环。**
  

#### **步骤 10: 指令转换与验证 (`ChangeSetGenerator`)**

  

*   **角色**: `ChangeSetGenerator` (LLM Agent)

*   **触发**: `_watch([ReviewNotes])` - 监听到总监的审阅笔记后启动。

*   **核心行动**: `GenerateChangeSet`

*   **输入**:

    1.  `ReviewNotes`消息。

    2.  当前的`FullDraft`消息（需要从`Environment`的`memory`中获取）。

*   **内部逻辑 (核心的验证-修复循环)**:

    1.  **指令转换尝试**: `Action`的Prompt要求LLM根据`ReviewNotes`和`FullDraft`内容，生成一个基于**上下文锚点**的`ChangeSet` JSON。

    2.  **语法验证**: `Action`的Python代码接收LLM的输出后，立刻执行`json.loads()`。

        *   **失败？-> 修复**: 如果解析失败，捕获异常，并将错误信息和错误的JSON字符串一起传回给LLM，Prompt为：“请修复以下JSON的格式错误：...”。此循环可重试2-3次。

    3.  **逻辑验证 (Dry Run)**: JSON格式正确后，代码遍历`ChangeSet`中的每条指令。对于每条指令，它会使用锚点ID（或锚点文本）在`FullDraft`中进行查找。

        *   **失败？-> 修复**: 如果某个锚点在文档中找不到，说明LLM幻觉出了错误的定位信息。此时，将此情况反馈给LLM，Prompt为：“你提供的锚点`{anchor}`在文档中未找到，请仔细阅读上下文，重新为这条修改意见 `{review_note}` 生成正确的定位和指令”。

*   **输出**: 一个**`ValidatedChangeSet`**消息，确保其内容是100%可被机器安全执行的。

  
#### **步骤 11: 精确修改执行 (`DocModifier`)**

*   **角色**: `DocModifier` (非LLM工具人)
*   **触发**: `_watch([ValidatedChangeSet])` - 只监听经过验证的指令集。
*   **核心行动**: `ExecuteChangeSet`
*   **输入**:
    1.  `ValidatedChangeSet`消息。
    2.  当前的`FullDraft`消息。
*   **内部逻辑 (Internal Logic)**:
    1.  **解析指令**: 遍历`ValidatedChangeSet`中的`changes`列表。
    2.  **定位与修改**: 对于每条指令，使用其锚点ID在`FullDraft`的文本中定位到精确位置。
    3.  **执行操作**: 根据`operation`字段（如`REPLACE_BLOCK`, `INSERT_AFTER`, `DELETE_SECTION`），对文本进行字符串操作。因为是纯代码执行，所以结果是确定和无误的。
    4.  **[风险与补充] 异常处理 (Exception Handling)**:
        *   **整个执行逻辑应被包裹在`try...except`块中。如果因任何原因（如锚点在并发操作中意外丢失）导致应用变更失败，它不应使流程崩溃，而应捕获异常，并发布一个`ModificationFailure`消息。此消息应包含失败的指令和原因，并被`ChangeSetGenerator`或`ChiefPM`监听，以触发对该指令的重新生成或人工干预。**
*   **输出**: 一个**新版本**的`FullDraft`消息。
  

#### **步骤 12: 修订循环机制 (The Revision Loop Mechanism)**

  

*   **消息驱动的自动流转**:

    1.  `DocModifier`输出的新版`FullDraft`消息被发布到`Environment`中。

    2.  由于`QAAgent`和`ChiefPM`都在`_watch`监听`FullDraft`消息，它们会被再次激活。

    3.  流程自动返回**步骤8**或**步骤9**，开始新一轮的“质检-审阅-指令-修改”循环。

  

*   **清晰的终止条件**:

    *   这个循环会持续进行，直到`ChiefPM`在**步骤9**中不再输出`ReviewNotes`，而是输出一个**`Approval`**消息。

    *   由于团队中没有任何角色`_watch` `Approval`消息来继续修订流程（`ChangeSetGenerator`和`DocModifier`不监听它），因此修订循环自然终止。

    *   监听`Approval`消息的`DocAssembler`的`FinalizeDocument`行动将被触发，流程平滑地进入下一阶段：最终交付。

  
  
  

### **阶段五：最终交付与报告 (Final Delivery & Reporting) - 详细展开版**

  

**核心目标**: 在文档被最终批准后，完成所有收尾工作，包括生成可交付的产物、提供过程度量衡报告，并为未来的项目迭代做好准备。

  

---

  

#### **步骤 13: 最终定稿与多格式输出 (`DocAssembler`)**

  

*   **角色**: `DocAssembler` (非LLM工具人)

*   **触发**: `_watch([Approval])` - 监听到`ChiefPM`的最终批准指令后启动。这是它在流程中的第二次（也是最后一次）主要行动。

*   **核心行动**: `FinalizeDocument`

*   **输入**:

    1.  `Approval`消息（作为触发信号）。

    2.  最终版本的`FullDraft`消息（从`Environment`的`memory`中获取）。

*   **细化的内部逻辑**:

    1.  **清理与净化**:

        *   **移除内部标记**: 使用正则表达式或专门的解析器，彻底移除所有在修订过程中使用的内部标记，包括上下文锚点ID (`[anchor-id::...]`)、行号等。

        *   **格式规范化**: 运行一遍Markdown linter（如`markdownlint`的Python库），自动修复一些轻微的格式问题，如多余的空行、不一致的标题格式等，确保最终输出的专业性。

    2.  **生成主交付物**:

        *   将净化后的内容保存为`final_document.md`。

    3.  **(增强) 多格式转换**:

        *   **理念**: 用户可能需要不同格式的文档。`DocAssembler`可以集成一个文档转换工具（如`pandoc`）。

        *   **实现**: 根据初始需求或配置，将最终的Markdown文件转换为其他格式。

            *   `pandoc final_document.md -o final_document.pdf`

            *   `pandoc final_document.md -o final_document.docx`

            *   `pandoc final_document.md -o final_document.html`

        *   这可以作为`FinalizeDocument`行动的一部分，使其交付能力更强。

*   **输出**:

    *   物理文件: `final_document.md`, `final_document.pdf`, `final_document.docx`等。

    *   一个`FinalDelivery`消息，内容可以包含所有生成文件的路径列表，用于通知其他收尾角色。

  

---

  

#### **步骤 14: 性能与成本报告 (`PerformanceMonitor`)**

  

*   **角色**: `PerformanceMonitor` (非LLM工具人)

*   **触发**: `_watch([Approval])` 或 `_watch([FinalDelivery])` - 在流程确认结束后启动。

*   **核心行动**: `GenerateReport`

*   **输入**: 无直接消息输入，但它在整个生命周期中已经通过监听`Environment`收集了所有数据。

*   **细化的内部逻辑**:

    1.  **数据聚合与计算**:

        *   遍历其记录的所有事件数据。

        *   **总成本**: 汇总所有LLM调用的预估成本。

        *   **按角色/行动分析**:

            *   计算每个`Role`和每个`Action`的总Token消耗（prompt tokens, completion tokens）。

            *   计算每个`Role`和每个`Action`的总API调用次数和平均耗时。

        *   **修订循环分析**:

            *   统计`ReviewNotes`消息被发布的次数，即总共进行了多少轮修订。

            *   分析每次修订循环的成本和耗时，以识别瓶颈。

    2.  **报告格式化**:

        *   将聚合后的数据格式化为易于阅读的JSON或Markdown报告。

        *   **(增强) 可视化**: 如果环境允许，可以生成简单的图表（如使用`matplotlib`保存为图片），展示各角色成本占比、各阶段耗时等，使报告更直观。

*   **输出**:

    *   物理文件: `performance_report.json` 和/或 `performance_summary.md`。

    *   这个报告对于评估SOP的效率、进行成本优化和发现性能瓶颈至关重要。

  

---

  

#### **(新增) 步骤 15: 项目归档与状态快照 (`Archiver`)**

  

*   **角色**: `Archiver` (一个新的非LLM工具人角色，可选)

*   **理念**: 一个完整的项目生命周期应该包含一个清晰的归档步骤，保存所有关键产物和过程数据，以便复盘、审计或基于此项目进行未来的增量开发。这与MetaGPT框架的`--inc`和序列化思想一脉相承，但在应用层做了更明确的封装。

*   **触发**: `_watch([FinalDelivery])` - 在所有文件生成完毕后启动。

*   **核心行动**: `ArchiveProject`

*   **输入**: `FinalDelivery`消息。

*   **内部逻辑**:

    1.  **创建归档目录**: 创建一个以项目名和时间戳命名的唯一归档文件夹，例如`archive/my_doc_project_20250420_103000/`。

    2.  **收集产物**:

        *   将**最终交付物**（`.md`, `.pdf`等）复制到归档目录。

        *   将**性能报告** (`performance_report.json`) 复制进来。

        *   将**所有关键的过程文档**（最终版的`PRD`, `SystemDesign`, `Task`等，这些可以从`Environment`的`memory`中根据消息类型过滤得到）也保存进来。

        *   将`ChiefPM`生成的所有`ReviewNotes`和`ChangeSetGenerator`生成的所有`ValidatedChangeSet`也保存起来，作为完整的**修订历史记录**。

    3.  **创建状态快照**:

        *   调用MetaGPT的序列化功能，将`Team`对象的最终状态（包含所有角色的最终记忆和状态）保存为一个`team_snapshot.json`文件。这对于未来使用`--recover-path`启动一个“克隆”项目或进行增量开发非常有价值。

    4.  **(增强) 版本控制**: 如果配置了git，可以自动将这个归档目录`git add`, `git commit -m "Project finalized"` 并 `git push` 到代码仓库。

*   **输出**: 一个`ProjectArchived`消息，标志着整个SOP流程的彻底、干净的结束。

  
  
  

### **5.0 附录 (Appendices)**

  

本附录提供了SOP V3.2实施过程中所需的关键配置、数据结构和Prompt范例，旨在为开发者提供清晰、可直接使用的参考。

  

#### **5.1. Agent 输入输出明细表 (V3.2)**

  

这张表格清晰地定义了每个角色的职责边界、信息流和依赖关系。

  

| 角色 (Role) | 核心行动 (Core Action) | 主要输入 (Primary Input) | 上下文策略 (Context Strategy) | 主要输出 (Primary Output) |

| :--- | :--- | :--- | :--- | :--- |

| **`ChiefPM`** | `DecomposeTopic` | 用户需求 `Message` | 直接输入 | `ProjectPlan` Message |

| | `ApproveTask` | `RefinedTask` Message | 无LLM，代码逻辑 | `ApprovedTask` Message |

| | `ReviewAndCommand` | `FullDraft` & `QAReport` | **1. `ContextOptimizer`压缩全文**<br>**2. Agent自主决策是否使用RAG进行核查** | `ReviewNotes` / `Approval` Message |

| **`GroupPM`** | `CreateModuleOutline` | 模块标题 `Message` | 探索式RAG，并将结果用于生成大纲和`rag_hint` | `ModuleOutline` Message |

| **`TaskDispatcher`** | `GenerateInitialTask` | 章节条目 `Message` | 直接输入 (快速LLM) | `InitialTask` Message |

| **`TaskRefiner`** | `RefineTask` | `InitialTask` Message | 直接输入 (CoT, 强LLM) | `RefinedTask` Message |

| **`TechnicalWriter`**| `WriteSection` | `ApprovedTask` Message | **1. 自主RAG/工具决策**<br>**2. `ContextOptimizer`处理组合上下文**<br>**3. 行动后自我反思** | `DraftSection` Message |

| **`QAAgent`** | `AutomatedCheck` | `FullDraft` Message | `ContextOptimizer`压缩长章节 | `QAReport` Message |

| **`ChangeSetGenerator`** | `GenerateChangeSet` | `ReviewNotes` & `FullDraft` | **验证-修复循环** | `ValidatedChangeSet` Message |

| **`DocAssembler`** | `AssembleDocument` | `list[DraftSection]` | 无LLM，注入上下文锚点 | `FullDraft` Message |

| | `FinalizeDocument` | `Approval` & `FullDraft` | 无LLM，移除锚点，多格式转换 | `FinalDelivery` Message & 物理文件 |

| **`DocModifier`** | `ExecuteChangeSet` | `ValidatedChangeSet` & `FullDraft` | 无LLM，基于锚点执行 | 新版本的 `FullDraft` Message |

| **`PerformanceMonitor`** | `GenerateReport` | `Approval` (触发信号) | 无LLM，聚合数据 | 物理文件 (`performance_report.json`) |

| **`Archiver`** | `ArchiveProject` | `FinalDelivery` (触发信号) | 无LLM，文件操作 | 物理归档目录 & `ProjectArchived` Message |

  

---

  

#### **5.2. 核心Prompt范例 (Core Prompt Examples)**

  

这些Prompt是Agent智能行为的核心驱动力。

  

*   **5.2.1. `TechnicalWriter`的自我反思Prompt (`_reflect`方法使用)**

  

    ```text

    You are a meticulous Quality Critic. Your task is to review a piece of writing based on an original request.

  

    **Original Request**:

    """

    {request}

    """

  

    **Generated Output**:

    """

    {output}

    """

  

    ---

    Please perform the following actions and respond in a single, valid JSON object:

    1.  **Evaluate**: Score the output from 1 to 5 on three criteria:

        a) **Completeness**: Does it fully address all aspects of the original request?

        b) **Clarity**: Is the language clear, concise, and easy to understand?

        c) **Accuracy**: Is the information factually correct and logically sound?

    2.  **Suggest**: Provide a brief, actionable suggestion for the single most important improvement. If no improvements are needed, state "None".

    3.  **Revise**: If the total score is less than 13, provide a revised, improved version of the output. Otherwise, the value should be an empty string.

  

    **Your JSON Response**:

    ```

  

*   **5.2.2. `ChangeSetGenerator`的指令转换Prompt**

  

    ```text

    You are a precise instruction conversion assistant. Your task is to convert a product director's natural language review notes into a structured JSON `ChangeSet`.

  

    **IMPORTANT RULES**:

    1.  You MUST use 'context anchors' for positioning. Find a short, unique text snippet from the original document (`anchor_text`) to locate the modification point. NEVER use line numbers.

    2.  The supported operations are: `REPLACE_BLOCK`, `INSERT_AFTER`, `DELETE_SECTION`.

    3.  For `DELETE_SECTION`, you must provide both `anchor_text_start` and `anchor_text_end`.

  

    **Product Director's Review Notes**:

    """

    {review_notes}

    """

  

    **Original Document Snippet for Context**:

    """

    {full_draft_snippet}

    """

  

    ---

    Now, generate the `ChangeSet` JSON object.

  

    **Your JSON `ChangeSet`**:

    ```

  

*   **5.2.3. `ContextOptimizer`的内部压缩Prompt**

  

    ```text

    You are an intelligent document compressor. Based on the user's high-level instruction, your goal is to extract the most relevant segments from the provided long context. Only return the extracted text, concatenated together.

  

    **User's High-Level Instruction**:

    """

    {instruction}

    """

  

    **Retrieved Relevant Chunks from Long Context**:

    """

    {retrieved_chunks}

    """

  

    ---

    **Your Compressed Context (only the essential text)**:

    ```

  

---

  

#### **5.3. `ChangeSet` JSON结构定义 (ChangeSet JSON Schema)**

  

这是`ChangeSetGenerator`生成、`DocModifier`消费的核心数据结构。

  

```json

{

  "$schema": "http://json-schema.org/draft-07/schema#",

  "title": "ValidatedChangeSet",

  "type": "object",

  "properties": {

    "changes": {

      "type": "array",

      "items": {

        "type": "object",

        "properties": {

          "operation": {

            "type": "string",

            "enum": ["REPLACE_BLOCK", "INSERT_AFTER", "INSERT_BEFORE", "DELETE_SECTION"]

          },

          "anchor_text": {

            "description": "A unique text snippet to locate the modification point. Used for single-point operations.",

            "type": "string"

          },

          "anchor_text_start": {

            "description": "The starting anchor for a range operation like DELETE_SECTION.",

            "type": "string"

          },

          "anchor_text_end": {

            "description": "The ending anchor for a range operation like DELETE_SECTION.",

            "type": "string"

          },

          "new_content": {

            "description": "The new content to be inserted or to replace the old content. Markdown formatted.",

            "type": "string"

          },

          "comment": {

            "description": "A brief explanation of why this change is being made.",

            "type": "string"

          }

        },

        "required": ["operation", "comment"]

      }

    }

  },

  "required": ["changes"]

}

```

  

---

  

#### **5.4. `config2.yaml` 推荐配置范例**

  

这是一个推荐的配置文件结构，展示了如何为SOP V3.2配置不同的资源。

  

```yaml

# MetaGPT

# version: 0.8.0

# ...

  

llm:

  api_type: "openai" # or "azure", "ollama", "gemini", etc.

  model: "gpt-4o-mini" # Default model for general tasks

  base_url: "https://api.openai.com/v1"

  api_key: "sk-..."

  max_token: 4096

  temperature: 0.7

  

# --- Role-specific LLM configurations can be injected at runtime ---

# This section is for components that read directly from config, like RAG.

  

rag:

  embedding:

    api_type: "openai"

    model: "text-embedding-3-small"

    dimensions: 1536

    api_key: "sk-..." # Can inherit from global if same

    base_url: "https://api.openai.com/v1"

  retriever:

    # Default retriever config, can be overridden in code

    top_k: 5

  

search:

  api_type: 'serpapi' # or 'google', 'serper', 'ddg'

  api_key: 'YOUR_SEARCH_API_KEY'

  

# Enable human-in-the-loop for key decisions

human_in_loop: true

  

# Project-specific settings

project_path: "./workspace"

archive_path: "./archive"

```


#### **5.5. 部署与运行检查清单 (Deployment & Runtime Checklist)**

在启动此多智能体系统前，请确保以下各项已准备就绪：

1. **[ ] 环境依赖**:
    
    - Python 版本 >= 3.9。
        
    - 已通过 pip install metagpt[rag,playwright,search] 安装所有必需的依赖项。
        
2. **[ ] 配置文件 (config2.yaml)**:
    
    - 已正确填写所有需要的LLM和工具的api_key及base_url。
        
3. **[ ] 环境变量**:
    
    - （如果使用）OPENAI_API_KEY等环境变量已正确设置。
        
4. **[ ] RAG知识库**:
    
    - 如果项目需要，已运行build_index.py脚本成功构建并持久化了RAG索引。
        
5. **[ ] 输入数据**:
    
    - 初始用户需求已准备好作为启动Team.run()的输入。


