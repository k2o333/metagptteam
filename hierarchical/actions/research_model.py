# mghier/hierarchical/actions/research_model.py (数据模型和配置)

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ToolExecutionStatus(Enum):
    """Tool execution status enumeration"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"


class ParsingStrategy(Enum):
    """JSON parsing strategy enumeration"""
    CODE_PARSER = "code_parser"
    MIXED_TEXT_JSON = "mixed_text_json"
    ACTION_PATTERNS = "action_patterns"
    MANUAL_TEXT_FORMAT = "manual_text_format"
    FALLBACK_JSON = "fallback_json"


@dataclass
class Context7ToolConfig:
    """Context7 MCP工具配置"""
    resolve_library_id_enabled: bool = True
    get_library_docs_enabled: bool = True
    library_id_format: str = "/org/project"
    version_specific_format: str = "/org/project/version"
    max_tokens_default: int = 10000
    retry_attempts: int = 3
    
    # 支持的库名称映射
    common_library_names: Dict[str, str] = field(default_factory=lambda: {
        "react": "/vercel/next.js",
        "next.js": "/vercel/next.js",
        "vue": "/vuejs/core",
        "angular": "/angular/angular",
        "django": "/django/django",
        "flask": "/pallets/flask",
        "express": "/expressjs/express",
        "mongodb": "/mongodb/docs",
        "tensorflow": "/tensorflow/tensorflow",
        "pytorch": "/pytorch/pytorch"
    })


@dataclass
class ResearchConfig:
    """Research action配置"""
    max_react_loops: int = 10
    max_parsing_attempts: int = 3
    tool_validation_enabled: bool = True
    provide_alternatives: bool = True
    
    # 解析配置
    parsing_strategies: List[ParsingStrategy] = field(default_factory=lambda: [
        ParsingStrategy.CODE_PARSER,
        ParsingStrategy.MIXED_TEXT_JSON,
        ParsingStrategy.ACTION_PATTERNS,
        ParsingStrategy.MANUAL_TEXT_FORMAT,
        ParsingStrategy.FALLBACK_JSON
    ])
    
    # 工具配置
    context7_config: Context7ToolConfig = field(default_factory=Context7ToolConfig)
    
    # 工具重试配置
    tool_retry_config: Dict[str, Any] = field(default_factory=dict)
    
    # 工具配置
    tools_config: Dict[str, Any] = field(default_factory=lambda: {
        "mcp_tools": [
            {
                "name": "resolve-library-id",
                "description": "Resolves a package/product name to a Context7-compatible library ID",
                "server": "context7"
            },
            {
                "name": "get-library-docs",
                "description": "Fetches up-to-date documentation for a library",
                "server": "context7"
            }
        ],
        "builtin_tools": [
            {
                "name": "use_internal_rag",
                "description": "Search internal documentation using RAG"
            }
        ]
    })
    
    # 提示词模板
    prompt_templates: Dict[str, str] = field(default_factory=lambda: {
        "base_system_prompt": (
            "You are an expert research assistant using a ReAct (Reasoning + Action) framework. "
            "Your goal is to systematically gather and analyze information to answer the user's question."
        ),
        "tool_instruction_template": (
            "**Available Tools:**\n{available_tools}\n\n"
            "**Context7 MCP Best Practices:**\n"
            "- Use two-step process: first call 'resolve-library-id' to get the exact library ID, then call 'get-library-docs'\n"
            "- For 'resolve-library-id': provide common library names like 'React', 'Next.js', 'Python', 'Django'\n"
            "- For 'get-library-docs': use the exact library ID returned from 'resolve-library-id' (format: /org/project or /org/project/version)\n"
            "- Optional parameters: topic (e.g., 'routing', 'hooks'), tokens (default: 10000)\n"
            "- When you have gathered sufficient information, use the FINISH tool with your analysis result."
        ),
        "completion_instruction": (
            "Based on the information gathered, provide a comprehensive answer to the original question. "
            "Structure your response clearly and cite specific information from the documentation when relevant."
        )
    })
    
    # 内置工具配置
    builtin_tools: Dict[str, Any] = field(default_factory=lambda: {
        "enable_document_analysis": True,
        "document_analysis_prompt": (
            "Please analyze the following documentation content and provide key insights:\n\n"
            "Documentation content:\n{documentation_content}\n\n"
            "Please provide a structured analysis including:\n"
            "1. Main topics covered\n"
            "2. Key features or functionalities\n"
            "3. Important configuration notes\n"
            "4. Usage examples if present"
        )
    })


@dataclass
class ToolExecutionResult:
    """Tool execution result data class"""
    status: ToolExecutionStatus
    source: str
    raw_data: Any = None
    reason: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ResearchStep:
    """Single research step data class"""
    step_number: int
    thought: str
    action: Dict[str, Any]
    observation: str
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "step_number": self.step_number,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "timestamp": self.timestamp
        }


@dataclass
class ResearchResult:
    """Research result data class"""
    query: str
    status: ToolExecutionStatus
    source: str
    final_answer: str
    steps_taken: int
    steps: List[ResearchStep] = field(default_factory=list)
    reason: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "query": self.query,
            "status": self.status.value,
            "source": self.source,
            "final_answer": self.final_answer,
            "steps_taken": self.steps_taken,
            "steps": [step.to_dict() for step in self.steps],
            "reason": self.reason,
            "execution_time": self.execution_time
        }


@dataclass
class LibraryResolutionResult:
    """Library resolution result data class"""
    library_name: str
    resolved_id: Optional[str] = None
    trust_score: Optional[float] = None
    code_snippets: Optional[int] = None
    description: Optional[str] = None
    error: Optional[str] = None
    
    def is_success(self) -> bool:
        """Check if resolution was successful"""
        return self.resolved_id is not None and self.error is None