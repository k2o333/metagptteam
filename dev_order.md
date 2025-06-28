
## **多智能体文档撰写系统 - 开发实施顺序 (SOP)**


### **第一阶段：项目初始化与核心数据结构 (Foundation & Schemas)**

**目标**: 搭建项目的骨架，定义所有Agent间通信的“语言”。这是整个系统的基石。

*   **第1步: 项目结构搭建与环境配置**
    *   **具体做什么**: 创建项目目录结构，配置虚拟环境，并安装基础依赖。
    *   **开发什么**:
        1.  按照开发文档 `3.0` 节，创建所有目录 (`configs/`, `metagpt_doc_writer/actions/`, `roles/`, `schemas/`, `tests/` 等)。
        2.  创建 `pyproject.toml` (或 `requirements.txt`)，并包含 `metagpt`, `pydantic`, `pytest`。
        3.  创建 `configs/config2.yaml` 配置文件，并填入你的LLM `api_key`。
    *   **达到什么标准**: 目录结构完整，`pip install -e .` 可以成功执行，项目包可被导入。
    *   **终端实际操作验收**:
        ```bash
        # 1. 验证目录结构
        tree metagpt-doc-writer/
        # 2. 安装并验证
        pip install -e .
        # 3. 运行一个简单的验证脚本
        python -c "from metagpt_doc_writer import roles; print('Setup OK')" 
        # 期望输出: Setup OK
        ```
    *   **测试脚本**: `tests/test_setup.py`
        ```python
        def test_import():
            # 简单验证包是否可以被成功导入
            from metagpt_doc_writer import schemas
            assert schemas is not None
        ```

*   **第2步: 定义所有核心数据结构 (Schemas)**
    *   **具体做什么**: 将文档中所有定义的消息体和数据结构，用 Pydantic 模型实现。
    *   **开发什么**: 在 `metagpt_doc_writer/schemas/doc_structures.py` 文件中，实现所有 `BaseModel` 子类，例如:
        *   `ProjectPlan`
        *   `ModuleOutline`
        *   `InitialTask`, `RefinedTask`, `ApprovedTask`
        *   `DraftSection`, `FullDraft`
        *   `ReviewNotes`, `Change`, `ValidatedChangeSet`
        *   `QAReport`, `FinalDelivery`, `ProjectArchived`
    *   **达到什么标准**: 所有数据结构定义完整，字段类型、描述和约束与开发文档一致。可以被成功实例化和验证。
    *   **终端实际操作验收**:
        ```bash
        # 创建一个脚本 `scripts/validate_schemas.py` 来实例化并打印一个复杂的Schema
        python scripts/validate_schemas.py
        # 期望输出: 成功实例化的Pydantic模型，无ValidationError
        ```
    *   **测试脚本**: `tests/schemas/test_doc_structures.py`
        ```python
        from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, Change

        def test_validated_changeset_creation():
            data = {
                "changes": [
                    {"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "Hello", "comment": "Test"}
                ]
            }
            # 验证数据可以被成功解析为Pydantic模型
            instance = ValidatedChangeSet(**data)
            assert len(instance.changes) == 1
            assert instance.changes[0].operation == "REPLACE_BLOCK"
        ```

---

### **第二阶段：确定性工具人角色开发 (Deterministic Roles)**

**目标**: 开发不依赖LLM、行为完全可预测的角色。它们是流程自动化和鲁棒性的保证。

*   **第3步: 实现 `DocAssembler` (文档组装工)**
    *   **具体做什么**: 开发组装和定稿文档的逻辑。
    *   **开发什么**:
        1.  `metagpt_doc_writer/roles/doc_assembler.py` 类，继承自 `Role`。
        2.  实现其 `_act` 方法的逻辑，用于处理 `AssembleDocument` 和 `FinalizeDocument` 两种情况。
        3.  `AssembleDocument` 逻辑：接收`list[DraftSection]`，排序并拼接，**核心是为每个段落注入唯一的锚点ID**。
        4.  `FinalizeDocument` 逻辑：接收`FullDraft`，**核心是移除所有锚点ID**，并保存为最终文件。
    *   **达到什么标准**: 能够正确地、确定地完成组装和清理任务。
    *   **终端实际操作验收**:
        ```bash
        # 创建脚本 `scripts/test_doc_assembler.py`
        # 脚本内创建几个DraftSection对象，喂给DocAssembler实例，并调用其方法
        python scripts/test_doc_assembler.py
        # 期望输出: 带有锚点的组合文本，以及清理后的最终文本
        ```
    *   **测试脚本**: `tests/roles/test_doc_assembler.py`
        ```python
        from metagpt_doc_writer.roles.doc_assembler import DocAssembler
        from metagpt_doc_writer.schemas.doc_structures import DraftSection

        def test_assemble_document_with_anchors():
            assembler = DocAssembler()
            sections = [
                DraftSection(chapter_id="1", content="Content A."),
                DraftSection(chapter_id="2", content="Content B.")
            ]
            # 模拟输入并调用内部方法
            result = assembler._assemble_with_anchors(sections)
            assert "[anchor-id::" in result
            assert "Content A." in result
            assert "Content B." in result
        
        # 同样为_finalize_document编写测试
        ```

*   **第4步: 实现 `DocModifier` (文档修改工)**
    *   **具体做什么**: 开发根据 `ValidatedChangeSet` 精确修改文档的逻辑。
    *   **开发什么**:
        1.  `metagpt_doc_writer/roles/doc_modifier.py` 类。
        2.  实现其 `_act` 方法，该方法调用一个核心的 `_apply_changes` 内部方法。
        3.  `_apply_changes` 逻辑：接收`FullDraft.content`和`list[Change]`，遍历`changes`，根据锚点ID和操作类型（`REPLACE_BLOCK`, `INSERT_AFTER`等）执行字符串替换/插入操作。
    *   **达到什么标准**: 对于任何合法的`ChangeSet`，都能精确无误地修改文本。
    *   **终端实际操作验收**:
        ```bash
        # 创建脚本 `scripts/test_doc_modifier.py`
        # 脚本内定义一个带锚点的文本和一个ChangeSet，喂给DocModifier实例
        python scripts/test_doc_modifier.py
        # 期望输出: 准确应用了变更后的新文本
        ```
    *   **测试脚本**: `tests/roles/test_doc_modifier.py`
        ```python
        from metagpt_doc_writer.roles.doc_modifier import DocModifier
        from metagpt_doc_writer.schemas.doc_structures import Change

        def test_apply_replace_block():
            modifier = DocModifier()
            content = "[anchor-id::abc]Old content.[anchor-id::def]"
            changes = [Change(operation="REPLACE_BLOCK", anchor_id="abc", new_content="New content.", comment="...")]
            new_content = modifier._apply_changes(content, changes)
            assert new_content == "[anchor-id::abc]New content.[anchor-id::def]"
        
        # 为INSERT_AFTER, DELETE_SECTION等操作编写更多测试
        ```

---

### **第三阶段：LLM驱动的角色与核心功能开发 (LLM-driven Roles & Core Features)**

**目标**: 逐步引入LLM，从最简单的任务开始，构建系统的核心智能。

*   **第5步: 实现 `TaskDispatcher` 和 `TaskRefiner`**
    *   **具体做什么**: 开发任务从粗到精的流水线。
    *   **开发什么**:
        1.  `actions/generate_initial_task.py` 和 `actions/refine_task.py`。
        2.  `roles/task_dispatcher.py` 和 `roles/task_refiner.py`。
        3.  为`refine_task` Action 设计 CoT (思维链) Prompt。
    *   **达到什么标准**: `TaskDispatcher`能快速生成任务描述。`TaskRefiner`能显著丰富任务细节，使其更具可执行性。
    *   **终端实际操作验收**:
        ```bash
        # 脚本 `scripts/test_task_pipeline.py`
        # 输入一个章节标题，依次通过Dispatcher和Refiner，打印每一步的输出
        python scripts/test_task_pipeline.py "Introduction to MetaGPT"
        # 期望输出: 打印InitialTask和内容更丰富的RefinedTask
        ```
    *   **测试脚本**: `tests/actions/test_refine_task.py`
        ```python
        import pytest
        from metagpt_doc_writer.actions.refine_task import RefineTask
        from metagpt_doc_writer.schemas.doc_structures import InitialTask

        @pytest.mark.asyncio
        async def test_refine_task_action(mocker):
            # 模拟LLM的返回
            mock_llm_response = '{"title": "...", "context": "...", "goals": ["..."]}'
            mocker.patch('metagpt.provider.base_llm.BaseLLM.aask', return_value=mock_llm_response)
            
            action = RefineTask()
            initial_task = InitialTask(chapter_title="Test Title")
            refined_task = await action.run(initial_task)
            assert refined_task.goals is not None
        ```

*   **第6步: 实现 `TechnicalWriter` (核心撰写功能)**
    *   **具体做什么**: 开发核心的内容生成角色，集成**自我反思**机制。
    *   **开发什么**:
        1.  `actions/write_section.py`: 实现`run`方法，其中包含**两次LLM调用**：一次生成初稿，第二次进行自我反思和修正。
        2.  `roles/technical_writer.py`: 组装`WriteSection` Action。
        3.  在`prompts/`目录下创建并引用`self_reflection_prompt`。
    *   **达到什么标准**: `WriteSection`的输出质量明显高于单次LLM调用。
    *   **终端实际操作验收**:
        ```bash
        # `scripts/test_technical_writer.py`
        # 输入一个RefinedTask，运行Writer，并打印其输出
        python scripts/test_technical_writer.py
        # 期望输出: 一个格式良好、内容充实的章节草稿
        ```
    *   **测试脚本**: `tests/actions/test_write_section.py`
        ```python
        # ... 类似于上一步，使用mocker模拟两次aask的调用
        # 第一次返回一个有瑕疵的初稿，第二次返回修正后的版本
        # 断言最终返回的是修正后的版本
        ```

*   **第7步: 实现修订循环 (`ChiefPM` + `ChangeSetGenerator`)**
    *   **具体做什么**: 开发将自然语言反馈转化为可执行修改指令的核心循环。
    *   **开发什么**:
        1.  `actions/review_and_command.py`: `ChiefPM`审阅并输出`ReviewNotes`。
        2.  `actions/generate_changeset.py`: **核心！** 实现**验证-修复循环**逻辑。在`run`方法中用`try-except`包裹LLM调用和JSON解析，如果失败，则使用一个专门的“修复Prompt”重试。
        3.  `roles/chief_pm.py` 和 `roles/changeset_generator.py`。
    *   **达到什么标准**: `GenerateChangeSet` Action**必须**总是输出一个100%合法的`ValidatedChangeSet` Pydantic模型，即使LLM初次返回的JSON是错误的。
    *   **终端实际操作验收**:
        ```bash
        # `scripts/test_revision_loop.py`
        # 输入一个带锚点的文档和一句修改意见（"把第一段改得更简洁"）
        # 运行ChiefPM -> ChangeSetGenerator -> DocModifier
        python scripts/test_revision_loop.py
        # 期望输出: 最终被成功修改后的文档
        ```
    *   **测试脚本**: `tests/actions/test_generate_changeset.py`
        ```python
        # 这个测试是关键
        @pytest.mark.asyncio
        async def test_changeset_repair_loop(mocker):
            # 第一次模拟LLM返回一个错误的JSON
            # 第二次模拟LLM返回一个正确的JSON
            mock_llm_calls = [
                '{"changes": [ ... malformed ...', # 第一次返回
                '{"changes": [{"operation": "REPLACE_BLOCK", ...}]}' # 第二次返回
            ]
            mocker.patch('metagpt.provider.base_llm.BaseLLM.aask', side_effect=mock_llm_calls)
            
            action = GenerateChangeSet()
            # ... 运行action ...
            # 断言aask被调用了两次，并且最终返回了合法的ValidatedChangeSet
        ```

---

### **第四阶段：集成、运行与监控 (Integration, Execution & Monitoring)**

**目标**: 将所有模块串联起来，形成一个完整的、可运行的系统，并添加监控能力。

*   **第8步: 端到端流程编排**
    *   **具体做什么**: 编写主入口脚本，将所有角色`hire`进一个`Team`，并启动流程。
    *   **开发什么**:
        1.  `run.py`: 创建`Team`实例，按顺序`hire`所有角色，调用`team.run_project(idea)`。
        2.  确保每个角色的 `_watch` 集合设置正确，以驱动消息流。
    *   **达到什么标准**: 系统能够从一个用户需求开始，完整地运行整个SOP，并生成一个初步的文档。
    *   **终端实际操作验收**:
        ```bash
        # 这是第一次真正运行整个系统
        python run.py "Write a simple tutorial about pytest."
        # 期望: 程序无错误运行，并在outputs/目录下生成final_document.md
        ```
    *   **测试脚本**: `tests/test_full_pipeline_integration.py`
        ```python
        # 这是一个更复杂的集成测试
        # 它会启动一个完整的Team，但使用mocked LLM来控制流程
        # 主要断言消息是否在角色间正确传递，以及最终文件是否被创建
        ```

*   **第9步: 实现 `PerformanceMonitor` 和 `Archiver`**
    *   **具体做什么**: 添加系统的度量和收尾能力。
    *   **开发什么**:
        1.  `roles/performance_monitor.py`: 一个非LLM角色，通过`_observe`所有消息，聚合token消耗、耗时等数据。
        2.  `roles/archiver.py`: 一个非LLM角色，在流程结束时被触发，负责收集所有产出物并保存到归档目录。
    *   **达到什么标准**: 运行结束后，生成一份准确的性能报告，并且所有产物被整齐地归档。
    *   **终端实际操作验收**:
        ```bash
        # 再次运行主流程
        python run.py "Another simple topic."
        # 运行结束后检查
        cat outputs/performance_report.json
        ls archive/
        # 期望: 看到json报告和归档文件夹
        ```
    *   **测试脚本**: `tests/roles/test_performance_monitor.py`
        ```python
        # 模拟一系列消息发布到环境中
        # 断言monitor最终生成的报告中的总成本、总token数是否计算正确
        ```
