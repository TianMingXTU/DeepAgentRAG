"""子智能体定义 — 同步子 Agent 字典。"""

from deeprag_coder.tools.code_analyze import code_analyze
from deeprag_coder.tools.doc_generate import doc_generate
from deeprag_coder.tools.graph_query import graph_query
from deeprag_coder.tools.rag_search import rag_search

code_analyzer_subagent = {
    "name": "code-analyzer",
    "description": "深度分析代码文件或函数的实现细节、依赖关系和调用链。适合复杂代码理解任务。",
    "system_prompt": """你是代码分析专家。使用 code_analyze 工具分析指定文件或函数的：
1. 实现逻辑和算法
2. 输入输出接口
3. 依赖关系和调用链
4. 潜在问题和改进建议

返回结构化分析报告，200 字以内。""",
    "tools": [code_analyze, graph_query, rag_search, doc_generate],
}

doc_generator_subagent = {
    "name": "doc-generator",
    "description": "为代码符号（函数、类、模块）生成文档和注释。需要理解代码上下文和项目风格。",
    "system_prompt": """你是文档生成专家。为指定的代码符号生成文档：
1. 分析代码逻辑和接口
2. 遵循项目的 docstring 风格
3. 生成中文 Google 风格文档（Args / Returns / Raises）

只返回生成的文档内容，100 字以内。""",
    "tools": [doc_generate, rag_search],
}

refactor_subagent = {
    "name": "refactor",
    "description": "执行跨文件代码重构，需要理解全局依赖和调用链。适合安全的重构操作。",
    "system_prompt": """你是重构专家。执行代码重构前：
1. 用 graph_query 分析函数的影响面
2. 用 rag_search 查找所有引用点
3. 确认重构安全后再执行

只返回重构计划和关键变更，200 字以内。""",
    "tools": [graph_query, rag_search, doc_generate],
}
