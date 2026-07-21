# DeepRAG-Coder — AI 项目说明书

## 项目概览

DeepRAG-Coder 是一个基于 **LangChain Deep Agents 框架** 和 **代码仓库 RAG 技术** 的智能编程助手。它将 Deep Agents 的任务规划/子智能体委派/虚拟文件系统等 Harness 能力，与 AST 语义分块/向量检索/知识图谱等代码专用 RAG 管道结合，让 AI 助手真正理解整个项目仓库。

**Python 版本**: >=3.12
**包管理器**: uv
**核心框架**: deepagents>=0.6.12 / langchain-openai / langchain-community / langgraph
**向量数据库**: chromadb (嵌入式, 零配置)
**代码解析**: tree-sitter >= 0.26 + tree-sitter-languages
**外部搜索**: Tavily (用于互联网调研)

---

## 构建与测试命令

```bash
# 安装全部依赖
uv sync

# 安装新增依赖（例如新增 langchain-chroma 时）
uv add <package-name>

# 验证 AST 解析器（解析 Python 样本，输出 3 个语义块为通过）
uv run python -m deeprag_coder.rag.chunker.ast_parser

# 验证语义分块器
uv run python -m deeprag_coder.rag.chunker.semantic_chunker

# 验证混合检索器
uv run python -m deeprag_coder.rag.retriever.hybrid_retriever

# 验证上下文组装器
uv run python -m deeprag_coder.rag.context_assembler

# 运行完整 Agent Demo
uv run python -m deeprag_coder.agent.deep_agent

# 运行单文件自检（所有 __main__ 内置 demo 均可用此方式调用）
uv run python path/to/module.py
```

---

## 代码风格指南

1. **Docstring 风格**: 中文 Google Style（`Args:` / `Returns:` / `Attributes:` 每个参数单独一行，缩进对齐）

2. **类型注解**: Python 3.10+ 原生语法
   - 用 `list[X]` 而非 `List[X]`
   - 用 `X | None` 而非 `Optional[X]`
   - 用 `dict[str, Any]` 而非 `Dict[str, Any]`

3. **导入风格**: 每个 import 独占一行，按 标准库 → 第三方库 → 本地模块 分组，组间空行

4. **模块级 Logger**: 每个 .py 文件顶部定义 `logger = logging.getLogger(__name__)`，方法内用 `logger.info/warning/error` 替代 `print`

5. **不写 `__init__.py`**: 利用 Python 3.12 隐式命名空间包，无需初始化文件

6. **Deep Agents Tool 的要求**: 
   - 函数必须有类型注解
   - 函数必须有 docstring（作为 Tool 的 description 被框架索引）
   - 可选参数必须有默认值

---

## 项目结构

```
deeprag_coder/
├── config/
│   └── settings.py            # 统一配置入口（LLM / RAG / Search / LangSmith）
├── agent/
│   └── deep_agent.py          # Deep Agents 装配（create_agent 工厂 + Tool 定义）
├── rag/
│   ├── chunker/
│   │   ├── ast_parser.py      # tree-sitter AST 解析 → CodeBlock / ParsedFile
│   │   └── semantic_chunker.py# CodeBlock 合并/拆分 → Chunk（可检索单元）
│   ├── embedder/
│   │   └── code_embedder.py   # LangChain OpenAIEmbeddings 封装
│   ├── vector_store/
│   │   ├── base.py            # VectorStore 抽象接口（VectorRecord）
│   │   └── chroma_store.py    # ChromaDB 持久化实现
│   ├── retriever/
│   │   └── hybrid_retriever.py# BM25 + 向量 加权融合检索（EnsembleRetriever）
│   ├── context_assembler.py   # 检索结果 → 结构化 Prompt 组装
│   └── pipeline.py            # RAG 管道总控（索引 + 检索 + 问答）
├── tools/                     # Agent Tool 定义（以 @tool 暴露）
│   ├── rag_search.py          # 语义搜索代码仓库
│   ├── rag_ask.py             # 基于 RAG 的代码问答
│   ├── graph_query.py         # 知识图谱查询（预留）
│   └── doc_generate.py        # 文档生成（预留）
└── skills/                    # Agent Skills（Agent Skills 规范）
    ├── code-review/           # 代码评审（预留）
    ├── refactor/              # 跨文件重构（预留）
    └── bug-hunt/              # Bug 定位（预留）
```

---

## 安全注意事项

1. **禁止硬编码密钥**: API Key / 密钥必须通过 `.env` 加载，由 `settings.py` 统一读取。`.env` 已在 `.gitignore` 中

2. **文件写保护**: Agent 的 `write_file` / `edit_file` 操作对 `deeprag_coder/` 目录被 `FilesystemPermission` 拒绝，防止 AI 误改自身源码

3. **`eval` 限制**: `calculate` tool 使用 `eval()`，仅在本地运行场景可用。生产环境中需替换为安全表达式求值

4. **LangSmith 追踪**: 开发阶段 `LANGSMITH_TRACING=true`，Key 仅在 `.env` 中

---

## 提交与协作规范

- **提交信息**: 遵循 Conventional Commits，如 `feat(rag): add hybrid retriever` / `fix(chunker): handle empty file`
- **新文件**: 在根目录 AGENTS.md 中同步更新项目结构
- **新增依赖**: 同时在 pyproject.toml 和本文件"核心依赖"部分更新
- **API Key 管理**: 永远不要提交 `.env` 文件。新增环境变量时在 `.env.example` 中记录占位