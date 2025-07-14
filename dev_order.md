

### **最终开发实施路线图：V4.5 "Artisan" (终极版)**

**总览**: 我们将严格按照官方建议，利用框架的内置能力，分四个阶段完成系统的全面升级。

---

### **Milestone 1 (不变): 实现统一的反思与优化循环**

**目标**: 为系统注入自我优化能力。

**要实现什么**:
1.  **创建`actions/reflect.py`及`ReflectAndOptimize` Action**。
2.  **（采纳官方建议）**在实现时，优先研究`metagpt.actions.write_review.py`，尝试使用`ActionNode`来构建一个结构化的、而不是基于简单Prompt模板的反思流程。如果`ActionNode`过于复杂，再降级为Prompt模板方案。
3.  **增强`CreatePlan` Action的Prompt**，使其能在`Plan`中插入`action_type: "REFLECT"`的任务。
4.  **修改`Executor`**以识别和处理`REFLECT`任务。

**需要注意的`metagpt`框架内容**:
*   **`metagpt.actions.ActionNode`**: 这是实现结构化、多步骤`Action`的核心工具。它能将一个复杂的任务（如“反思”）分解为多个内部小步骤（如“评估完整性”、“评估清晰度”、“生成建议”、“综合修订”），使`Action`的逻辑更清晰、结果更可控。

**如何验收**:
1.  `Plan`中包含`action_type: "REFLECT"`的任务。
2.  日志显示`Executor`成功调用了`ReflectAndOptimize` Action。
3.  `REFLECT`任务的`result`是基于其依赖任务结果优化后的新版本。

---

### **Milestone 2 (重大重构): 实现基于`metagpt`原生能力的分层LLM资源调度**


#### **第一步：重构`config2.yaml`以符合官方标准**

这是所有修改的基础。

```yaml
# /root/.metagpt/config2.yaml (最终官方标准版)

# 全局默认LLM，当Action没有指定llm_name_or_type，
# 且其所属Role也没有指定默认llm_key时使用。
llm:
  api_type: "openai"
  model: "llama3-8b-instruct"
  base_url: "http://192.168.88.7:4000/v1"
  api_key: "sk-1234"

# 【核心修正】使用'models'块来定义所有可用的具名LLM配置
models:
  deepseek_v3_base:
    api_type: "openai"
    model: "deepseek-v3"
    base_url: "http://192.168.88.7:4000/v1"
    api_key: "sk-1234"
  deepseek_r1_cot:
    api_type: "openai"
    model: "deepseek-r1"
    base_url: "http://192.168.88.7:4000/v1"
    api_key: "sk-1234"
  gpt_4o_strong:
    api_type: "openai"
    model: "gpt-4o"
    api_key: "sk-your_real_key"

# 【核心修正】使用'roles'块为角色绑定默认的LLM key
roles:
  - role: "ChiefPM" # 与Role类的name属性匹配
    llm_key: "gpt_4o_strong"
  - role: "Executor"
    llm_key: "deepseek_r1_cot" # Executor默认使用这个

# 【核心设计】我们自己的自定义配置块，用于定义高级资源池
# 官方建议，这种自定义配置可以放在这里，由我们的应用代码自己加载和解析
role_action_llm_pools:
  "ChiefPM-CreatePlan":
    - "gpt_4o_strong"
    - "deepseek_r1_cot" # 备用
  "Executor-Research":
    - "deepseek_v3_base"
    - "deepseek_r1_cot" # 并行/备用
  "Executor-REFLECT": # 假设我们有一个REFLECT Action
    - "gpt_4o_strong"
    - "deepseek_r1_cot"
```

---

#### **第二步：重构`run.py`，简化资源管理**

`run.py`现在不再需要创建LLM池，只需要加载配置，创建`Context`即可。

```python
# /root/metagpt/mgfr/scripts/run.py (部分修改)

# ...

async def main(idea: str, ...):
    # ... (配置加载)
    with open(config_yaml_path, 'r', encoding='utf-8') as f:
        full_config = yaml.safe_load(f)

    # --- 2. 创建Context ---
    # Config会自动加载'llm', 'models', 'roles'等标准块
    config = Config.from_yaml_file(config_yaml_path)
    ctx = Context(config=config)

    # --- 3. 【核心修改】将我们的自定义配置放入Context的kwargs中 ---
    # 这是官方推荐的、用于存储自定义数据的安全方式
    ctx.kwargs.role_action_llm_pools = full_config.get("role_action_llm_pools", {})
    
    # ... (MCP管理器初始化) ...
    # 之后将ctx传递给所有角色
    chief_pm = ChiefPM(context=ctx)
    executor = Executor(context=ctx)
    # ...
```

---

#### **第三步：重构`Executor`和`Action`，实现最终的调度逻辑**

这是本次修改的核心，完全拥抱`metagpt`的原生机制。

##### **`/root/metagpt/mgfr/metagpt_doc_writer/roles/executor.py` (最终版)**

`Executor`的职责是：
1.  从`Context`中读取资源池配置。
2.  根据`Task`和资源池配置，决定要使用哪些LLM `key`。
3.  **动态实例化**`Action`，并将`llm_name_or_type`传递给它。
4.  实现并行和故障回退逻辑。

```python
# /root/metagpt/mgfr/metagpt_doc_writer/roles/executor.py

from .base_role import DocWriterBaseRole
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import Task
from metagpt_doc_writer.actions.research import Research
from metagpt_doc_writer.actions.write import Write
from metagpt_doc_writer.actions.review import Review
from typing import Dict, List, Type
import asyncio

class Executor(DocWriterBaseRole):
    name: str = "Executor"
    profile: str = "Task Executor"
    goal: str = "Execute tasks using dynamically scheduled resources."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 不再在init时创建Action实例，而是存储Action的类
        self.action_classes: Dict[str, Type[Action]] = {
            "RESEARCH": Research,
            "WRITE": Write,
            "REVIEW": Review,
            # "REFLECT": ReflectAndOptimize, # 未来可以添加
        }

    async def run(self, task: Task, completed_tasks: Dict[str, Task]) -> Task:
        logger.info(f"Executor received task '{task.task_id}' with type '{task.action_type}'.")
        
        action_class = self.action_classes.get(task.action_type)
        if not action_class:
            task.result = f"Error: No action class found for type '{task.action_type}'"
            return task

        # 1. 从Context获取资源池配置
        role_action_pools = self.context.kwargs.get("role_action_llm_pools", {})
        action_key = f"{self.__class__.__name__}-{action_class.__name__}"
        
        # 2. 决定本次任务要使用的LLM key列表
        # 任务指定 > Role-Action池 > Role默认 > 全局默认
        default_llm_key = self.config.roles.get(self.name, {}).get("llm_key")
        llm_keys_to_use = role_action_pools.get(action_key, [default_llm_key] if default_llm_key else [])

        if not llm_keys_to_use:
            logger.warning(f"No specific LLM pool found for {action_key}, using global default LLM.")
            # 如果没有找到任何配置，Action初始化时不传llm_name_or_type，会使用全局默认llm
        
        # 3. 准备上下文 (与之前相同)
        context_str = "..."

        # 4. 实现并行与故障回退的执行逻辑
        # 假设我们将instruction分解为多个子任务来并行
        sub_instructions = [task.instruction] # 简化：先只处理一个子任务

        async def execute_subtask(sub_instr, llm_keys):
            for i, key in enumerate(llm_keys):
                try:
                    logger.info(f"Attempting subtask with LLM: '{key}'")
                    action_instance = action_class(llm_name_or_type=key, context=self.context)
                    
                    # 准备kwargs
                    action_kwargs = {"instruction": sub_instr, "context": context_str, ...}
                    
                    return await action_instance.run(**action_kwargs)
                except Exception as e:
                    logger.warning(f"Subtask failed with LLM '{key}'. Error: {e}. Trying next fallback LLM.")
                    if i == len(llm_keys) - 1: # 如果是最后一个也失败了
                        logger.error(f"All fallback LLMs failed for subtask. Aborting.")
                        return f"Error: All LLMs failed. Last error: {e}"
        
        # 并发执行所有子任务 (当前只有一个)
        tasks_to_gather = [execute_subtask(si, llm_keys_to_use) for si in sub_instructions]
        results = await asyncio.gather(*tasks_to_gather)
        
        task.result = "\n\n".join(results)
        return task
```

##### `/root/metagpt/mgfr/metagpt_doc_writer/actions/research.py` (简化版)
`Action`现在变得极其纯粹，它不再关心资源和权限，只负责执行。

```python
# /root/metagpt/mgfr/metagpt_doc_writer/actions/research.py

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar
from metagpt.tools.search_engine import SearchEngine

class Research(Action):
    # ... (PROMPT_TEMPLATE不变) ...
    
    # run方法现在非常干净
    async def run(self, instruction: str, context: str = "", **kwargs) -> str:
        logger.info(f"Executing Research Action for: '{instruction}'")
        
        # Action不再关心是否启用搜索，它被调用时就意味着应该搜索
        try:
            search_engine = SearchEngine()
            search_result = await search_engine.run(instruction)
            # ...
        except Exception as e:
            # ...
        
        # ... 组合prompt并调用LLM ...
        # 注意：这里的 self.llm 已经被框架根据 llm_name_or_type 动态设置好了
        result = await self._aask(...)
        return result
```

### **总结：一个真正“可编排”的架构**

通过这次最终的、基于官方权威反馈的重构，我们的系统架构达到了前所未有的高度：

1.  **配置即编排**: 我们的`config2.yaml`现在是一份真正的“编排文件”。它精确地定义了每个`Role`的每个`Action`在执行时可以使用的**模型资源池**和**故障回退策略**。
2.  **原生能力最大化**: 我们完全利用了`metagpt`内置的`models`配置、`Context`共享机制和`Action(llm_name_or_type=...)`的动态调度能力，代码量更少，但功能更强大。
3.  **职责分离完美**: `Planner(ChiefPM)`负责“做什么”，`Executor`负责“用什么资源去做”，`Action`负责“怎么做”。三者权责分明，高度解耦。



### **优化后的Milestone 2验收标准 (终极版)**

**核心目标**: 验证系统能否根据`config2.yaml`中的`models`和`role_action_llm_pools`配置，为不同的`Task`动态、正确地调度`LLM`资源。

我们将通过三个独立的、可量化的测试用例（Test Case）来完成验收。

---

#### **Test Case 1: 验证“Role-Action特定资源池”的调度能力**

**目的**: 验证系统是否能为一个特定的`Role-Action`组合（如`Executor-Research`）使用其专用的LLM池，而不是`Executor`角色的默认LLM。

**准备工作 (配置)**:
1.  在`config2.yaml`的`models`块中，定义三个清晰可辨的模型key，例如：
    *   `strong_model`: `gpt-4o`
    *   `research_model`: `deepseek-v3`
    *   `default_model`: `llama3-8b-instruct`
2.  在`roles`块中，为`Executor`设置默认LLM：
    *   `role: "Executor"`, `llm_key: "default_model"`
3.  在`role_action_llm_pools`块中，为`Executor-Research`专门配置一个资源池：
    *   `"Executor-Research": ["research_model"]`
4.  确保`ChiefPM`生成的`Plan`中，第一个任务是`action_type: "RESEARCH"`，并且**不包含**`llm_config_key`字段。

**执行**:
*   运行主脚本 `python scripts/run.py ...`

**验收标准**:
*   **日志必须清晰地显示**:
    1.  `Executor`在处理`RESEARCH`任务时，打印出类似`"Attempting subtask with LLM: 'research_model'"`的日志。
    2.  如果后续有`WRITE`任务，`Executor`在处理它时，应打印出`"Attempting subtask with LLM: 'default_model'"`的日志（因为它没有在`role_action_llm_pools`中特殊指定，所以使用了`Executor`的默认模型）。
*   **结果验证**: `RESEARCH`任务的产出内容应符合`deepseek-v3`的风格和质量。

**通过这个测试，我们能100%确认系统正确地解析了`role_action_llm_pools`配置，并实现了Role-Action级别的资源覆盖。**

---

#### **Test Case 2: 验证“Task级LLM指定”的最高优先级**

**目的**: 验证在`Task`中直接指定的`llm_config_key`具有最高优先级，能覆盖`Role-Action`池和`Role`的默认配置。

**准备工作 (配置)**:
1.  保持与Test Case 1相同的`config2.yaml`配置。
2.  **修改`CreatePlan`的Prompt**，让它为第一个`RESEARCH`任务**明确地指定**`llm_config_key`。
    *   在`CREATE_PLAN_PROMPT`中，修改示例，让LLM知道可以这样做。例如：`"For critical research, you can specify 'llm_config_key': 'strong_model' to ensure the highest quality."`
    *   或者，为了测试，我们可以手动修改`ChiefPM`返回的`Plan`，为第一个`Task`硬编码`llm_config_key: "strong_model"`。

**执行**:
*   运行主脚本。

**验收标准**:
*   **日志必须清晰地显示**:
    *   `Executor`在处理第一个`RESEARCH`任务时，打印出`"Attempting subtask with LLM: 'strong_model'"`。
    *   这个结果证明了`Task`级别的指定，成功覆盖了`Executor-Research`资源池中定义的`research_model`。
*   **结果验证**: `RESEARCH`任务的产出内容应符合`gpt-4o`的风格和质量。

**通过这个测试，我们能确认LLM调度的优先级体系（Task > Role-Action > Role > Global）是正确工作的。**

---

#### **Test Case 3: 验证“故障回退（Fallback）”机制**

**目的**: 验证当资源池中的首选LLM失败时，系统能否自动、优雅地切换到池中的下一个备用LLM。

**准备工作 (配置与代码)**:
1.  **配置一个会失败的LLM**: 在`config2.yaml`的`models`块中，为一个模型（比如`research_model`）故意配置一个**错误的API Key**或一个**不存在的`base_url`**。
2.  **配置一个带备用的资源池**: 在`role_action_llm_pools`中，为`Executor-Research`配置一个包含主力和备用的池：
    *   `"Executor-Research": ["research_model", "default_model"]`
3.  确保`ChiefPM`生成的`Plan`中，`RESEARCH`任务不指定`llm_config_key`，以便它使用这个资源池。

**执行**:
*   运行主脚本。

**验收标准**:
*   **日志必须清晰地显示**:
    1.  `Executor`首先打印`"Attempting subtask with LLM: 'research_model'"`。
    2.  紧接着，打印一条**警告或错误**日志，内容为`"Subtask failed with LLM 'research_model'. Error: ... Trying next fallback LLM."`。
    3.  然后，打印一条新的尝试日志：`"Attempting subtask with LLM: 'default_model'"`。
    4.  最后，任务成功完成。
*   **功能验证**: 整个流程没有因为第一个LLM的失败而中断，而是成功地用备用模型完成了任务并继续执行后续流程。

**通过这个测试，我们能证明我们系统的核心优势之一——健壮性——是真实有效的。**





#### **3. `Executor.run`的最终实现**

这是整个动态调度逻辑的核心，现在它将完全依赖`metagpt`的内置机制。

```python
# /root/metagpt/mgfr/metagpt_doc_writer/roles/executor.py (最终实现)

# ... (imports) ...

class Executor(DocWriterBaseRole):
    # ... (__init__不变, set_actions([Research, Write, Review])) ...

    async def run(self, task: Task, completed_tasks: Dict[str, Task]) -> Task:
        logger.info(f"Executor received task '{task.task_id}' with type '{task.action_type}'.")
        
        # 1. 根据action_type找到对应的Action类
        action_class = next((type(act) for act in self.actions if act.name == task.action_type), None)
        
        if not action_class:
            task.result = f"Error: No action class found for type '{task.action_type}'"
            logger.error(task.result)
            return task

        # 2. 【核心】动态实例化Action，并通过llm_name_or_type传递LLM key
        #    如果task.llm_config_key为None，则Action会自动使用Executor的默认LLM。
        #    metagpt框架会处理LLM的创建和注入。
        logger.info(f"Instantiating action '{action_class.__name__}' with LLM key: '{task.llm_config_key or 'Role default'}'.")
        action_instance = action_class(
            llm_name_or_type=task.llm_config_key,
            context=self.context # 将共享上下文传递给Action
        )
        
        # 3. 准备其他参数并执行
        context_str = "\n\n---\n\n".join([
            # ... (上下文拼接逻辑不变)
        ])
        
        action_kwargs = {
            "instruction": task.instruction,
            "context": context_str,
            # ... (其他参数准备逻辑不变)
        }
        
        action_result = await action_instance.run(**action_kwargs)
        task.result = action_result
        
        return task
```

#### **4. `CreatePlan` Action的增强**

我们需要确保`ChiefPM`在生成`Plan`时，能为需要强推理的任务（如`REFLECT`）分配`"strong_model"`。

```python
# /root/metagpt/mgfr/metagpt_doc_writer/actions/create_plan.py (Prompt增强)

CREATE_PLAN_PROMPT = """
You are an expert project manager...
Each task must have:
...
- An optional `llm_config_key`. For tasks requiring deep reasoning, creativity, or reflection (like 'REFLECT'), set this to "strong_model". For most standard tasks, you can omit this field to use the default model.
...
"""
```


### **Milestone 3 (优化): 实现带限流的并发任务处理**

**目标**: 在实现并行的基础上，增加并发控制，防止API超限。

**要实现什么**:
1.  修改`run.py`主循环，使用`asyncio.gather`并发执行任务。
2.  **（采纳官方建议）**在`run.py`中，为需要限流的LLM API创建一个`asyncio.Semaphore`，并将其放入共享的`Context`中。例如：`ctx.strong_model_semaphore = asyncio.Semaphore(3)`。
3.  修改`Executor`，让它在调用`Action`前，检查该`Action`将要使用的LLM是否需要限流。如果需要，则在`await action_instance.run(...)`的调用外层包裹`async with ctx.strong_model_semaphore:`。

**需要注意的`metag-pt`框架内容**:
*   **`cost_manager`并发安全**: 通过`Semaphore`限制对同一LLM实例的并发调用，是保护`cost_manager`的最佳实践。
*   **`Context`共享**: 将`Semaphore`放入`Context`是向所有角色广播这个“共享锁”的最优雅方式。

**如何验收**:
1.  日志显示并行任务几乎同时开始。
2.  即使有大量并行任务请求同一个强模型，API也不会因为速率超限而报错。

---

### **Milestone 4 (优化): 实现基于持久化路径的RAG**

**目标**: 采纳官方建议，使用更健壮的、基于路径的RAG持久化和加载机制。

**要实现什么**:
1.  创建`scripts/build_rag_index.py`，它将索引持久化到磁盘上的一个固定路径，例如`./storage/rag_index`。
2.  修改`run.py`，在启动时不再直接加载引擎，而是将**索引路径**放入`Context`中，例如`ctx.rag_index_path = "./storage/rag_index"`。
3.  修改`Research` Action（或其他需要RAG的Action），让它在`run`方法内部，通过`SimpleEngine.from_storage(context_path=self.context.rag_index_path)`来**即时加载**RAG引擎。

**需要注意的`metagpt`框架内容**:
*   **`SimpleEngine.from_storage()`**: 这是官方推荐的从持久化数据中恢复RAG引擎的方法。
*   **懒加载**: 在`Action`内部即时加载，而不是在`run.py`启动时就加载，可以加快程序的启动速度，并降低内存的常驻开销。

**如何验收**:
1.  `Research` Action的日志显示它成功从指定路径加载了RAG引擎。
2.  最终产出中包含了来自本地知识库的、非网络搜索能得到的内容。

