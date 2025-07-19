
### **重构方案：从线性调度到深度优先迭代**

我们将分四个核心阶段进行重构。

#### **阶段一：奠定基石 —— 新的数据模型**

这是所有重构的基础。我们需要用能够表达“树状结构”和“状态”的新数据模型，来替换或增强现有的扁平化`Plan`和`Task`。

1.  **修改 `metagpt_doc_writer/schemas/doc_structures.py`**
    *   **引入 `Section` 和 `Outline`**: 这是整个新架构的核心。根据你们的讨论，创建这两个 Pydantic 模型。
        ```python
        # In metagpt_doc_writer/schemas/doc_structures.py
        
        from pydantic import BaseModel, Field
        from typing import List, Optional, Dict, Any
        from datetime import datetime
        import uuid

        class Section(BaseModel):
            """代表文档中的一个章节或子章节，是文档树的节点。"""
            section_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
            display_id: str = Field("", description="用于展示的、带层级的ID，如 '1', '1.2'")
            title: str
            level: int
            content: str = ""
            status: str = Field("PENDING_OUTLINE", description="生命周期状态: PENDING_WRITE, WRITING, PENDING_REVIEW, COMPLETED, PENDING_SUBDIVIDE")
            version: int = 1
            last_modified: datetime = Field(default_factory=datetime.now)
            parent_id: Optional[str] = None
            sub_sections: List['Section'] = Field(default_factory=list)
            # 存储为该章节写作提供的上下文，如研究资料
            research_data: str = ""

        # 确保 Pydantic V2+ 能正确处理前向引用
        Section.model_rebuild()

        class Outline(BaseModel):
            """代表整个文档的、可演化的树状结构。"""
            goal: str
            root_sections: List[Section] = Field(default_factory=list)

            # 关键辅助方法：通过ID在整个树中查找、更新、添加节点
            def find_section(self, section_id: str, search_in: Optional[List[Section]] = None) -> Optional[Section]:
                # ... 实现递归查找 ...
            
            def add_sub_sections(self, parent_id: str, sub_sections: List[Section]):
                # ... 实现添加子章节的逻辑 ...

            def update_section_content(self, section_id: str, new_content: str):
                # ... 实现更新章节内容的逻辑 ...

            def get_sections_by_status(self, status: str) -> List[Section]:
                # ... 实现根据状态查找所有章节的逻辑 ...
        ```
    *   **废弃/改造旧模型**：您现有的`Plan`和`Task`模型是为线性工作流设计的。在新架构下，`Outline`将取代`Plan`成为顶层结构。`Task`的概念将被内化到`Section`的状态流转中。可以暂时保留这些旧文件，但在新逻辑中不再使用。

---

#### **阶段二：重塑大脑 —— Planner 和 Executor 的新职责**

`Planner`不再是只执行一次的计划者，而是整个迭代过程的“大脑”；`Executor`则从一次处理一个任务，变成并行处理一批章节。

1.  **重构 `metagpt_doc_writer/roles/`**
    *   **创建一个新的 `Planner` Role (或重构 `ChiefPM`)**
        *   **核心状态**: 这个`Planner` Role的核心`memory`现在应该是那个全局的`Outline`对象。
        *   **核心`Action`**: 创建一个新的`CreateSubOutline` Action。
            ```python
            # In a new actions/create_sub_outline.py
            
            class CreateSubOutline(Action):
                # ...
                async def run(self, parent_section: Section, full_outline: Outline, research_data: str = "") -> List[Section]:
                    # 1. 构建智能上下文 (面包屑+父内容)
                    # 2. 调用LLM，让它只生成一个标题列表 (e.g., ["1.1 Core Concepts", "1.2 Key APIs"])
                    # 3. 在Action代码中，为每个标题生成新的Section对象，并设置正确的 section_id, display_id, level, parent_id
                    # 4. 返回新创建的Section列表
            ```
        *   **核心 `_act` 逻辑 (循环控制器)**:
            ```python
            # In Planner Role's _act method
            
            # 1. 检查Outline中是否有状态为 `PENDING_SUBDIVIDE` 的章节
            section_to_expand = self.outline.find_next_section_to_expand()
            
            if section_to_expand:
                # (可选) 为其启动一个Research Action
                research_results = await self.research_action.run(topic=section_to_expand.title)
                
                # 为该章节创建子大纲
                new_sub_sections = await self.create_sub_outline_action.run(
                    parent_section=section_to_expand, 
                    full_outline=self.outline,
                    research_data=research_results
                )
                
                # 更新全局大纲，并将新章节状态设置为 PENDING_WRITE
                self.outline.add_sub_sections(section_to_expand.section_id, new_sub_sections)
                
                # 发送消息，将这批新章节交给Executor
                return Message(content="dispatching new sections for writing", instruct_content=new_sub_sections, send_to="Executor")

            # 2. 如果没有要扩展的，检查是否有章节需要从 COMPLETED 变成 PENDING_SUBDIVIDE
            #    这是决定是否继续“深挖”的逻辑
            if self.should_deepen_further(self.outline):
                 # ... 标记某个章节为 PENDING_SUBDIVIDE，然后下一轮循环就会处理它
            
            # 3. 如果一切都完成了，发出结束信号
            return Message(content="ALL_TASKS_COMPLETED")
            ```

    *   **重构 `Executor` Role**
        *   **监听**：`Executor`应该`_watch` `Planner`发出的 `List[Section]` 消息。
        *   **核心 `_act` 逻辑 (并行处理器)**:
            ```python
            # In Executor Role's _act method
            
            # 1. 从消息中获取要处理的Section列表
            sections_to_process = self.rc.msg.instruct_content
            
            # 2. 创建并发任务
            # 【Milestone 3 优化点】
            # 从 self.context 中获取 Semaphore
            # strong_model_semaphore = self.context.kwargs.get('strong_model_semaphore')

            coroutines = []
            for section in sections_to_process:
                # 为每个section创建一个完整的“写-审-改”工作流协程
                workflow_coro = self.process_section_workflow(section, self.outline)
                coroutines.append(workflow_coro)
                
            # 3. 并发执行所有工作流
            results = await asyncio.gather(*coroutines)
            
            # 4. 更新全局Outline，并将完成的章节状态设置为 COMPLETED
            for section_id, final_content in results:
                self.outline.update_section_content(section_id, final_content)

            # 5. （可选）向Planner发送一个完成回执
            return Message(content=f"Completed processing {len(results)} sections.")
            ```
        *   **新增 `process_section_workflow` 辅助方法**:
            ```python
            # In Executor Role, a new helper method
            
            async def process_section_workflow(self, section: Section, full_outline: Outline) -> (str, str):
                # 【Milestone 3 优化点】
                # async with strong_model_semaphore:
                #    ...
                
                # 1. 构建写入上下文 (面包屑+父内容+兄弟标题)
                write_context = build_writing_context(full_outline, section.section_id)
                
                # 2. 调用 Write Action
                draft = await self.write_action.run(section=section, context=write_context)
                
                # 3. 调用 Review Action
                review_comments = await self.review_action.run(draft=draft, section=section)
                
                # 4. 调用 Revise Action
                final_content = await self.revise_action.run(draft=draft, comments=review_comments, section=section)

                # 5. 返回元组 (section_id, final_content)
                return (section.section_id, final_content)
            ```

---

#### **阶段三：重构主流程和并发控制**

您当前的 `run.py` 是一个线性的任务调度器。我们需要一个全新的主控流程来支持新架构，并在这里实现并发控制。

1.  **重构 `scripts/run.py`**
    *   **移除旧的调度循环**：删除 `while len(completed_tasks) < len(plan.tasks):` 循环。
    *   **初始化核心对象**:
        ```python
        # In new run.py
        
        async def main(idea: str):
            # 1. 初始化 Context 和 Config
            ctx = Context(...)
            
            # 2. 【Milestone 3 优化点】创建并注入Semaphore
            ctx.kwargs['strong_model_semaphore'] = asyncio.Semaphore(3) # 限制并发数为3

            # 3. 初始化全局唯一的 Outline 对象
            outline = Outline(goal=idea)
            
            # 4. 初始化 Roles，并将 outline 和 ctx 传递给它们
            #    这确保了它们共享同一个文档状态树和上下文
            planner = Planner(context=ctx, outline=outline)
            executor = Executor(context=ctx, outline=outline)
            
            # 5. 创建一个简化版的 Team 或直接手动调度
            team = Team(context=ctx)
            team.hire([planner, executor])
            
            # 6. 启动流程
            await team.run_project(idea) # Team会处理消息循环
            
            # 7. 流程结束后，从 outline 对象中提取最终文档
            final_document = assemble_final_document(outline)
            # ... 保存文档 ...
        ```
    *   **实现最终文档拼接函数 `assemble_final_document`**: 这个函数会递归遍历`outline`对象，按照`display_id`的顺序，将所有`Section`的`content`拼接成一个完整的Markdown文件。

---

#### **阶段四：Action 层面的精细化**

最后，我们需要确保`Action`接收到正确的、最小化的上下文。

1.  **修改 `metagpt_doc_writer/actions/`**
    *   **更新 `Write` Action (`write.py`)**
        *   `run`签名: `async def run(self, section: Section, context: Dict[str, Any]) -> str:`
        *   `Prompt`设计: 使用您和同事讨论过的模板，该模板包含`{breadcrumbs}`, `{parent_content}`, `{sibling_titles}`等占位符。
    *   **更新 `Review` Action (`review.py`)**
        *   `run`签名: `async def run(self, draft: str, section: Section) -> str:`
    *   **更新 `Revise` Action (`revise.py`)**
        *   `run`签名: `async def run(self, draft: str, comments: str, section: Section) -> str:`

### **总结与建议**

这个重构方案是一个比较大的工程，但它能完全实现您设想的先进架构。

*   **从简单开始**：先不要实现并发，用`for`循环代替`asyncio.gather`，确保整个深度优先的迭代逻辑跑通。
*   **日志是关键**：在`Planner`和`Executor`的每个决策点（如`find_next_section_to_expand`, `build_writing_context`）都打印详细日志，这将是调试的生命线。
*   **充分利用`Context`**: 将`Semaphore`、全局`Outline`（如果选择这种共享方式）等放入`Context`是`metagpt`框架中最优雅的共享状态的方式。

好的，为每个重构阶段设计一个相对简单的验收方法，让您能快速验证核心功能是否正确实现。这些方法主要依赖于**日志输出**和**最终文件检查**，避免了复杂的单元测试配置。

---

### **阶段一：奠定基石 —— 新的数据模型**

**目标**: 验证 `Section` 和 `Outline` Pydantic模型能否正确地构建、操作和序列化一个树状结构。

**简单的验收方法**: 创建一个独立的测试脚本。

1.  **创建一个新文件**: 在 `scripts/` 目录下创建一个 `test_schemas.py` 文件。
2.  **编写测试代码**: 在这个文件中，手动创建和操作您的新模型。

    ```python
    # in scripts/test_schemas.py
    import json
    from mgfr.metagpt_doc_writer.schemas.doc_structures import Outline, Section

    def run_schema_test():
        print("--- 阶段一验收：测试数据模型 ---")

        # 1. 创建一个空的 Outline
        my_outline = Outline(goal="测试文档结构")

        # 2. 添加顶级章节
        intro_section = Section(display_id="1", title="Introduction", level=1)
        core_section = Section(display_id="2", title="Core Concepts", level=1)
        my_outline.root_sections.extend([intro_section, core_section])
        
        print("✅ 成功创建顶级大纲。")

        # 3. 为“Core Concepts”添加子章节
        sub_sections_data = [
            {"display_id": "2.1", "title": "Concept A", "level": 2},
            {"display_id": "2.2", "title": "Concept B", "level": 2},
        ]
        new_sub_sections = [Section(**data, parent_id=core_section.section_id) for data in sub_sections_data]
        
        # 假设您已在Outline中实现 add_sub_sections 方法
        core_section.sub_sections.extend(new_sub_sections)
        
        print("✅ 成功添加子章节。")

        # 4. 更新一个子章节的内容
        # 假设您已在Outline中实现 find_section 和 update_section_content 方法
        target_section = my_outline.find_section(new_sub_sections[0].section_id)
        if target_section:
            target_section.content = "这是Concept A的详细内容。"
            target_section.status = "COMPLETED"
            print("✅ 成功更新子章节内容。")

        # 5. 打印最终的JSON结构以供人工检查
        print("\n--- 最终Outline结构 (JSON) ---")
        print(json.dumps(my_outline.model_dump(), indent=2))
        print("\n--- 验收标准 ---")
        print("请检查以上JSON输出：")
        print("1. 'root_sections'下是否有两个顶级章节？")
        print("2. 'Core Concepts'章节下是否有'sub_sections'列表，且包含两个子章节？")
        print("3. 'Concept A'子章节的'content'和'status'是否已更新？")

    if __name__ == "__main__":
        run_schema_test()
    ```

**如何验收**:
直接运行 `python scripts/test_schemas.py`。
*   如果脚本无错误地运行完毕，并且**打印出的JSON结构**符合最后提示的三个检查点，那么您的数据模型就已成功奠基。

---

### **阶段二：重塑大脑 —— Planner 和 Executor 的新职责**

**目标**: 验证 `Planner` 能生成子大纲，并将其正确地传递给 `Executor` 进行处理，完成一次迭代。

**简单的验收方法**: 使用**Mocking（模拟）**和**日志**来测试核心逻辑流，而无需真实的LLM调用。

1.  **修改Action**: 暂时修改 `CreateSubOutline` 和 `Write/Review/Revise` Action，让它们返回固定的、可预测的结果。

    ```python
    # In actions/create_sub_outline.py
    class CreateSubOutline(Action):
        async def run(...) -> List[Section]:
            logger.info("MOCK: Returning hardcoded sub-sections.")
            # 返回一个硬编码的列表，而不是调用LLM
            return [Section(title="Mocked Sub-Section 1.1", ...)]

    # In roles/executor.py's process_section_workflow
    async def process_section_workflow(...):
        logger.info(f"MOCK: Processing section {section.display_id}")
        # 不调用真实的Action，直接返回结果
        return (section.section_id, f"Final mocked content for {section.title}")
    ```

2.  **编写一个简化的主循环**:
    *   创建一个 `Outline` 对象，其中包含一个顶级章节，并将其状态设置为 `PENDING_SUBDIVIDE`。
    *   实例化 `Planner` 和 `Executor`，让它们共享这个 `Outline` 对象。
    *   手动调用 `planner._act()`。
    *   获取 `planner` 返回的消息，并手动调用 `executor._act()`（将该消息作为输入）。

**如何验收**:
*   **检查日志**:
    *   `Planner` 的日志应显示它正在为 `PENDING_SUBDIVIDE` 的章节创建子大纲。
    *   `Executor` 的日志应显示它接收到了新的子章节列表，并正在（用mock方式）处理它们。
*   **检查最终状态**: 在 `executor._act()` 执行完毕后，检查共享的 `Outline` 对象。
    *   新的子章节（如 "Mocked Sub-Section 1.1"）应该已经被添加。
    *   这些新子章节的 `content` 字段应该被填充为 `"Final mocked content for ..."`。
    *   它们的状态应该被更新为 `COMPLETED`。

如果日志流和最终的`Outline`状态都符合预期，说明`Planner`和`Executor`之间的核心迭代逻辑已经打通。

---

### **阶段三：重构主流程和并发控制**

**目标**: 验证 `run.py` 的新主循环能够并行调度任务，并且 `Semaphore` 能有效限流。

**简单的验收方法**: 通过**日志的时间戳和特定日志的出现顺序**来可视化并发行为。

1.  **配置并发测试环境**:
    *   在 `run.py` 中，将 `Semaphore` 的并发数设置为一个较小的值，例如 `2`。`ctx.kwargs['strong_model_semaphore'] = asyncio.Semaphore(2)`
    *   （暂时）修改 `Planner`，让它在第一轮就生成一个包含4个或更多章节的顶级大纲，这样 `Executor` 就能一次性收到4个并行的任务。

2.  **在Executor中埋点**: 在 `Executor` 的 `process_section_workflow` 方法中添加带延时的日志记录。

    ```python
    # In roles/executor.py
    async def process_section_workflow(self, section: Section, ...):
        semaphore = self.context.kwargs.get('strong_model_semaphore')
        logger.info(f"Task for '{section.title}' is READY, waiting for semaphore.")
        
        async with semaphore:
            logger.success(f"Task for '{section.title}' ACQUIRED semaphore. Starting work...")
            await asyncio.sleep(3)  # 模拟长时间的LLM调用
            final_content = f"Content for {section.title}"
            logger.info(f"Task for '{section.title}' FINISHED work, releasing semaphore.")
        
        return (section.section_id, final_content)
    ```

**如何验收**:
运行 `python scripts/run.py` 并仔细观察日志。理想的输出顺序应该是：
1.  几乎在**同一时间**，打印出 **4条** `"Task for '...' is READY..."` 日志。
2.  紧接着，**只有2条** `"Task for '...' ACQUIRED semaphore..."` 日志被打印。
3.  等待3秒。
4.  打印出 **2条** `"Task for '...' FINISHED work..."` 日志，并且**几乎同时**，另外 **2条** `"Task for '...' ACQUIRED semaphore..."` 日志出现。
5.  再等待3秒，最后2条 `"FINISHED work"` 日志出现。

这个特定的日志模式清晰地证明了：所有任务都已准备好，但 `Semaphore(2)` 成功地将并发执行的“工人”数量限制在了2个。

---

### **阶段四：Action 层面的精细化**

**目标**: 验证 `Write` Action 在为深层级章节生成内容时，其接收到的 Prompt 是正确的、包含足够上下文的。

**简单的验收方法**: **打印并人工检查 Prompt**。

1.  **设置测试场景**: 运行完整的系统，目标是生成一个至少有两层结构的大纲（例如，`1. Introduction` -> `1.1 What is it?`）。
2.  **修改 `Write` Action**: 在 `Write` Action的 `run` 方法中，在调用 `self._aask()` 之前，将最终要发送给LLM的 `prompt` 完整地打印到控制台。为了不真的消耗token，可以暂时注释掉 `_aask` 调用并返回一个模拟字符串。

    ```python
    # In actions/write.py
    async def run(self, section: Section, context: Dict[str, Any]) -> str:
        # ... 这里是您构建 prompt 的逻辑 ...
        prompt = self.PROMPT_TEMPLATE.format(
            breadcrumbs=context.get("breadcrumbs"),
            parent_content=context.get("parent_content"),
            # ...
        )

        # --- 验收关键点 ---
        print("\n" + "="*80)
        print(f"DEBUG: PROMPT FOR WRITING SECTION '{section.display_id}: {section.title}'")
        print(prompt)
        print("="*80 + "\n")
        # --------------------

        # return await self._aask(prompt) # 暂时注释掉
        return f"Mock content for {section.title}"
    ```

**如何验收**:
*   当系统运行到撰写二级标题（如 "1.1 What is it?"）时，**在控制台检查打印出的 Prompt**。
*   确认 Prompt 中**必须包含**以下几个关键部分：
    *   **面包屑路径**: 类似 `DOCUMENT STRUCTURE (YOU ARE HERE): \n- 1. Introduction\n - 1.1 What is it?`
    *   **父章节内容**: `CONTENT OF THE PARENT SECTION ("1. Introduction"): ...`
    *   **兄弟章节标题**: `OTHER SECTIONS AT THE SAME LEVEL: ...`


如果打印出的Prompt结构清晰，内容符合预期，就证明您的上下文构建逻辑是正确的。