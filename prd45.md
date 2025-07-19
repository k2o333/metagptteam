

### **技术需求文档 (PRD)：多智能体文档系统 V4.5**

**版本**: 4.5
**代号**: "Artisan" (工匠)
**核心目标**: 在当前稳定的串行调度架构基础上，引入**并发执行、智能反思、高级上下文管理**和**精细化资源调度**能力，实现生产效率和产出质量的飞跃。

---

#### **1. 核心需求与设计原则**

1.  **【并发执行】并行任务处理 (Parallel Task Processing)**
    *   **用户故事**: "作为一个项目经理，我希望计划中那些没有依赖关系的任务（例如，同时研究两个不同主题，或撰写两个独立章节）能够被**并行处理**，以显著缩短整个项目的交付时间。"
    *   **技术要求**:
        *   `run.py`中的主调度器需要从“一次只取一个就绪任务”升级为“一次性获取**所有**就绪任务”。
        *   利用`asyncio.gather`并发执行所有就绪任务的`executor.run()`调用。
        *   必须确保`completed_tasks`字典的更新操作是**并发安全**的。虽然在单个`asyncio`事件循环中，简单的字典赋值是原子的，但在复杂的`await`前后，需要审慎处理状态。

2.  **【智能优化】统一的反思与优化循环 (Unified Reflection & Optimization Loop)**
    *   **用户故事**: "我希望系统不仅能完成任务，还能像一个真正的专家一样，对自己的产出（无论是任务计划、草稿还是最终文档）进行**自我审视和优化**，以提高质量，减少返工。"
    *   **技术要求**:
        *   创建一个新的、通用的`ReflectAndOptimize` Action。
        *   `ChiefPM`在生成`Plan`时，有能力在关键节点后插入`action_type: "REFLECT"`的任务。
        *   `REFLECT`任务的`instruction`字段将被用作“反思标准/视角”（`criteria`）。
        *   `Executor`需要能处理`REFLECT`任务，它会找到其依赖任务的`result`作为“产出物”（`artifact`），连同`criteria`一起传递给`ReflectAndOptimize` Action。

3.  **【高级上下文】增量式RAG上下文管理 (Incremental RAG Context Management)**
    *   **用户故事**: "我希望系统能处理一个大型的、预先存在的知识库（如一个项目的所有背景文档），并在执行任务时，能**智能地、快速地**从这个知识库中检索相关信息作为上下文，而不是依赖实时的、不稳定的网络搜索。"
    *   **技术要求**:
        *   提供一个离线脚本（如`scripts/build_rag_index.py`），用于预先构建一个持久化的RAG索引。
        *   `Research` Action（或其他任何`Action`）的`run`方法需要能加载这个预构建的索引。
        *   `Action`的`run`方法将使用任务的`instruction`作为查询，对RAG索引进行`aretrieve()`，并将检索到的内容注入到最终的Prompt中。
        *   **【增量】**（V4.5高级特性）：对于需要长期记忆的`Role`，可以为其配备一个内部的RAG引擎实例，在每次行动后将关键记忆`add`到索引中，实现增量式记忆。

4.  **【精细化资源】分层LLM资源调度 (Hierarchical LLM Resource Scheduling)**
    *   **用户故事**: "我希望能够为不同的任务类型或角色配置不同性能和成本的LLM，例如，让规划和反思任务使用最强的模型，而简单的写作任务使用更经济的模型，以优化成本。"
    *   **技术要求**:
        *   扩展`config2.yaml`，允许定义一个**LLM池（LLM Pool）**，包含多个带有别名的LLM配置。
        *   扩展`Task` Schema，增加一个可选的`llm_config_key`字段。
        *   `ChiefPM`在生成`Plan`时，可以为特定`Task`指定其应使用的LLM配置的`key`。
        *   `Executor`在执行`Task`时，检查`task.llm_config_key`。如果存在，则从一个全局的LLM实例管理器中获取对应的LLM实例，并用它来执行该任务；如果不存在，则使用`Executor`默认的LLM。

---

#### **2. 架构与模块设计变更**

##### **a. `config2.yaml`**
```yaml
# ... (llm, rag, search等配置不变)

# 【新增】LLM池定义
llm_pool:
  strong_model:
    model: "gpt-4o"
    api_key: "sk-..."
    base_url: "..."
    # ...
  fast_model:
    model: "llama3-8b-instruct"
    api_key: "sk-..."
    base_url: "..."
    # ...

# 【新增】角色-默认LLM绑定
role_llm_bindings:
  ChiefPM: "strong_model"
  Executor: "fast_model"

# ... (mcp_servers, role_mcp_bindings等不变)
```

##### **b. `schemas/doc_structures.py`**
```python
class Task(BaseModel):
    # ... (其他字段不变)
    llm_config_key: Optional[str] = Field(None, description="The key of the LLM config from the pool to use for this task.")
```

##### **c. `scripts/run.py` (主调度器)**
*   在`main`函数开始时，根据`config2.yaml`中的`llm_pool`初始化一个LLM实例字典。
*   在初始化`Role`时，根据`role_llm_bindings`为其注入默认的LLM实例。
*   **修改主循环**:
    ```python
    # while循环内
    ready_tasks = plan.get_ready_tasks(list(completed_tasks.keys()))
    if not ready_tasks: break

    # 并发执行所有就绪的任务
    tasks_to_run = [executor.run(task, completed_tasks, llm_pool) for task in ready_tasks]
    results = await asyncio.gather(*tasks_to_run)

    # 并发安全地更新结果
    for updated_task in results:
        completed_tasks[updated_task.task_id] = updated_task
        logger.success(f"Task '{updated_task.task_id}' completed.")
    ```

##### **d. `roles/executor.py`**
*   `run`方法签名变更为 `async def run(self, task: Task, completed_tasks: Dict[str, Task], llm_pool: Dict[str, BaseLLM]) -> Task:`。
*   内部逻辑:
    1.  确定要使用的LLM：
        ```python
        target_llm = self.llm # 默认LLM
        if task.llm_config_key and task.llm_config_key in llm_pool:
            target_llm = llm_pool[task.llm_config_key]
            logger.info(f"Using LLM '{task.llm_config_key}' for task '{task.task_id}'.")
        ```
    2.  找到`Action`后，手动为其注入选定的`LLM`实例：`action_to_run.set_llm(target_llm)`。
    3.  继续执行`Action`。

##### **e. 新增 `actions/reflect.py`**
```python
from metagpt.actions import Action

class ReflectAndOptimize(Action):
    name: str = "REFLECT"
    PROMPT_TEMPLATE: str = """
    Your role is to act as a critic and optimizer.
    Based on the following criteria, please review the provided artifact and return an improved version.
    If no improvements are necessary, return the original artifact.

    CRITERIA:
    ---
    {criteria}
    ---

    ARTIFACT TO REVIEW:
    ---
    {artifact}
    ---

    Your improved artifact:
    """
    
    async def run(self, criteria: str, artifact: str, **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(criteria=criteria, artifact=artifact)
        return await self._aask(prompt)
```

---

#### **3. 验收标准**

*   **AC1 (并发)**: 当`Plan`中有多个无依赖的任务时（如两个并行的`RESEARCH`任务），日志显示它们是**几乎同时**开始执行的。
*   **AC2 (反思)**: 当`Plan`中包含一个`REFLECT`任务时，`Executor`能正确调用`ReflectAndOptimize` Action，并且该任务的`result`是基于其依赖任务`result`（`artifact`）和自身`instruction`（`criteria`）优化后的内容。
*   **AC3 (RAG)**: 当一个`Task`的`instruction`需要本地知识时，`Research` Action能够加载本地索引并返回相关内容（需要一个本地文档和索引构建脚本作为测试支持）。
*   **AC4 (分层LLM)**: 当一个`Task`指定了`llm_config_key`时，日志清晰地显示`Executor`为该任务切换到了指定的LLM模型。

