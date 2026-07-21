# DeepRAG-Coder 开发计划

## 一、项目目标与核心功能梳理（对齐 readme.md）

DeepRAG-Coder 目标：构建一个**开箱即用、深度理解代码仓库**的 AI 编程助手，融合 Deep Agents 框架 + 代码专用 RAG 管道。

核心能力清单：

| #   | 功能                | 描述                                     |
| --- | ------------------- | ---------------------------------------- |
| F1  | **代码问答**        | 自然语言询问代码逻辑、API 用法、模块依赖 |
| F2  | **智能代码补全**    | 基于全仓库上下文（非单文件）进行语义补全 |
| F3  | **跨文件重构**      | 理解全局依赖后安全重构                   |
| F4  | **代码审查**        | 基于最佳实践和历史修复实例评审           |
| F5  | **文档生成**        | 自动生成项目文档、API 文档、代码注释     |
| F6  | **Bug 定位与修复**  | 语义检索定位问题 + 历史修复建议          |
| F7  | **新手上手**        | 为新开发者提供仓库导航和解答             |
| F8  | **任务规划与委派**  | 主智能体规划 + 子智能体执行              |
| F9  | **虚拟文件系统**    | 读写编辑搜索代码文件                     |
| F10 | **上下文管理**      | 自动压缩/卸载上下文                      |
| F11 | **持久化记忆**      | 跨会话记忆召回                           |
| F12 | **人机协作**        | 关键决策点暂停等待审批                   |
| F13 | **Skills 技能系统** | 可复用行为模块按需加载                   |
| F14 | **MCP 原生支持**    | 标准协议连接外部工具                     |
| F15 | **代码解释器**      | QuickJS 运行时执行代码片段               |
| F16 | **AST 语义分块**    | Tree-sitter AST 解析保障分块完整性       |
| F17 | **语义向量检索**    | 向量嵌入 + 混合检索（BM25 + 嵌入）       |
| F18 | **仓库知识图谱**    | 符号节点 + 调用关系边 + LLM 语义摘要     |
| F19 | **上下文感知生成**  | 融合问题 + 代码片段 + 全局结构为 prompt  |

其中 F8-F15 由 Deep Agents 框架**原生提供**，只需正确的参数配置即可激活；F16-F19 是**本项目的增量构建**——需开发代码专用 RAG 管道并注册为自定义 Tool/Skill。

---

## 二、整体架构与模块划分

基于 Deep Agents 的三层架构（Runtime→Framework→Harness）和 Middleware 扩展模型，项目架构如下：

```
deeprag_coder/
├── __init__.py                    # 版本号、公开 API 导出
├── cli/                           # CLI 入口 (dcode 风格)
│   └── main.py                    # Typer CLI: init, search, ask, review
├── agent/                         # 智能体层 —— Deep Agents 编排
│   ├── factory.py                 # create_deeprag_agent() 工厂函数
│   ├── prompts.py                 # 系统提示词（编码专家角色）
│   ├── profiles.py                # Harness Profiles（按模型调优）
│   ├── subagents.py               # 子智能体定义（同步+异步）
│   └── permissions.py             # 文件系统权限规则
├── rag/                           # RAG 代码库层 —— 本项目的核心增量
│   ├── pipeline.py                # RAG 管道总控（初始化/更新/检索/组装）
│   ├── chunker/                   # 代码分块
│   │   ├── ast_parser.py          # Tree-sitter AST 解析器
│   │   └── semantic_chunker.py    # AST 引导的语义分块策略
│   ├── embedder/                  # 向量嵌入
│   │   └── code_embedder.py       # 代码嵌入模型封装
│   ├── vector_store/              # 向量数据库
│   │   ├── base.py                # 抽象接口
│   │   └── chroma_store.py        # Chroma 实现（默认，零配置）
│   ├── retriever/                 # 检索策略
│   │   ├── hybrid_retriever.py    # BM25 + 向量混合检索
│   │   └── reranker.py            # 结果重排序
│   ├── knowledge_graph/           # 知识图谱
│   │   ├── builder.py             # 图谱构建器（符号+调用关系）
│   │   └── querier.py             # 图谱查询器
│   └── context_assembler.py       # 上下文组装（问题+代码+结构→prompt）
├── tools/                         # 暴露给 Agent 的 LangChain Tool
│   ├── rag_search.py              # rag_search: 语义搜索代码仓库
│   ├── rag_ask.py                 # rag_ask: 基于 RAG 上下文问答
│   ├── graph_query.py             # graph_query: 查询知识图谱
│   ├── code_analyze.py            # code_analyze: 代码分析（依赖链、影响面）
│   └── doc_generate.py            # doc_generate: 生成文档/注释
├── skills/                        # Skills 目录（Agent Skills 规范）
│   ├── code-review/               # 代码评审 Skill
│   │   ├── SKILL.md
│   │   └── references/            # 评审规则、反模式清单
│   ├── refactor/                  # 跨文件重构 Skill
│   │   ├── SKILL.md
│   │   └── references/            # 重构策略、依赖分析指南
│   ├── doc-gen/                   # 文档生成 Skill
│   │   ├── SKILL.md
│   │   └── references/            # 文档模板、风格指南
│   └── bug-hunt/                  # Bug 定位 Skill
│       ├── SKILL.md
│       └── references/            # 常见 Bug 模式
├── memory/                        # 持久化记忆配置
│   └── project_context.py         # 项目上下文：AGENTS.md、仓库摘要
└── config/                        # 配置管理
    ├── settings.py                # 环境变量 + 默认值
    └── model_profiles.py          # 模型-Profile 映射表
```

**与 Deep Agents 框架的对接关系：**

| 本项目模块                  | Deep Agents 接入点                       | 对接方式                                                                                                         |
| --------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `agent/factory.py`          | `create_deep_agent()`                    | 主入口：传入 model, tools, system_prompt, subagents, skills, backend, permissions, memory, interrupt_on, profile |
| `tools/*`                   | `tools=[...]` 参数                       | 标准 LangChain Tool（types + docstring + defaults）                                                              |
| `skills/*`                  | `skills=[...]` 参数                      | Agent Skills 规范目录，按 Progressive Disclosure 加载                                                            |
| `memory/project_context.py` | `memory=[...]` 参数 + `CompositeBackend` | AGENTS.md 注入 + `/memories/` → StoreBackend 路由                                                                |
| `rag/pipeline.py`           | 不直接对接框架，由 Tool 调用             | RAG 管道作为 Tool 的内部引擎                                                                                     |
| `agent/profiles.py`         | `profile=HarnessProfile(...)` 参数       | 微调通用子智能体、上下文压缩触发条件                                                                             |
| `agent/subagents.py`        | `subagents=[...]` 参数                   | 同步 SubAgent 字典 + AsyncSubAgent                                                                               |
| `agent/permissions.py`      | `permissions=[...]` 参数                 | FilesystemPermission 声明式规则                                                                                  |

---

## 三、开发阶段与里程碑

### 阶段 0：环境与依赖就绪（0.5 天）

**目标**：补齐 pyproject.toml 依赖，确保 Deep Agents 可运行。

**任务：**
| # | 任务 | 输入 | 输出 | 依赖 |
|---|---|---|---|---|
| 0.1 | 添加 RAG 相关依赖到 pyproject.toml：`tree-sitter`, `chromadb`, `rank-bm25` | 技术栈清单 | 完整依赖声明 | — |
| 0.2 | 配置 LangSmith 追踪环境变量 | .env 模板 | 可追踪的运行环境 | 0.1 |
| 0.3 | 验证 `create_deep_agent()` 最小示例可运行 | deep_agent.py | 确认框架可用 | 0.2 |

**依赖变更（pyproject.toml 追加）：**

```toml
"tree-sitter>=0.24.0",
"chromadb>=0.6.0",
"rank-bm25>=0.2.2",
"rich>=13.0.0",        # CLI 美化输出
"typer>=0.15.0",       # CLI 框架
```

---

### 阶段 1：RAG 管道核心 — 代码感知检索（3-4 天）

**目标**：实现 AST 分块 → 向量嵌入 → 混合检索 → 上下文组装这条完整链路。

#### 1.1 AST 解析与语义分块

| #     | 任务                                                            | 输入          | 输出                                                                                         | 依赖  | 难点                                                        |
| ----- | --------------------------------------------------------------- | ------------- | -------------------------------------------------------------------------------------------- | ----- | ----------------------------------------------------------- |
| 1.1.1 | 选型并集成 Tree-sitter 语言包（Python/TS/JS/Go/Java/Rust 优先） | language list | `ast_parser.py`：通用 AST 解析器，根据文件扩展名选择 parser                                  | 0.3   | 多语言 parser 的编译安装；需处理解析失败降级                |
| 1.1.2 | 实现语义分块策略：按函数/类/方法边界切分，保留 import 头        | AST 节点树    | `semantic_chunker.py`：输出 `[{path, chunk_id, content, start_line, end_line, symbol_name}]` | 1.1.1 | 嵌套结构（class 内 method）的分块粒度抉择；大文件的拆分策略 |
| 1.1.3 | 仓库扫描入口：遍历目录，过滤无关文件，调用分块                  | 仓库根路径    | 分块列表 + 进度日志                                                                          | 1.1.2 | node_modules/.git/venv 等噪声目录过滤                       |

#### 1.2 向量嵌入与存储

| #     | 任务                                                         | 输入                | 输出                                         | 依赖  | 难点                                                        |
| ----- | ------------------------------------------------------------ | ------------------- | -------------------------------------------- | ----- | ----------------------------------------------------------- |
| 1.2.1 | 封装嵌入模型：默认用 OpenAI `text-embedding-3-small`，可切换 | model config        | `code_embedder.py`：`embed(texts) → vectors` | 0.3   | 大批量分块的嵌入速率控制（batch + rate limit）              |
| 1.2.2 | Chroma 向量库实现：`add`, `search`, `delete`, `persist`      | chunks + embeddings | `chroma_store.py`：持久化向量索引            | 1.2.1 | Collection 命名空间隔离（多项目共存）；metadata schema 设计 |
| 1.2.3 | 增量更新策略：对比文件 hash，仅重索引变化文件                | 旧索引 + 新仓库状态 | 增量更新 diff                                | 1.2.2 | checksum 计算性能与准确度平衡                               |

#### 1.3 混合检索

| #     | 任务                                              | 输入           | 输出                 | 依赖         | 难点                                  |
| ----- | ------------------------------------------------- | -------------- | -------------------- | ------------ | ------------------------------------- |
| 1.3.1 | BM25 关键词检索：对分块内容建 BM25 索引           | chunks         | `BM25Okapi` 索引对象 | 1.1.3        | 中文/多语言分词器的选择               |
| 1.3.2 | 混合检索 + 融合排名：BM25 + 向量相似度 → 加权融合 | query + 双索引 | 排序结果列表         | 1.2.2, 1.3.1 | 融合策略：RRF vs 线性加权，需实验验证 |
| 1.3.3 | 可选重排序：用 LLM 对 Top-K 二次精排              | Top-K chunks   | 重排结果             | 1.3.2        | 延迟与精度权衡；可设为可选开关        |

#### 1.4 上下文组装

| #     | 任务                                                     | 输入                      | 输出                   | 依赖  | 难点                                           |
| ----- | -------------------------------------------------------- | ------------------------- | ---------------------- | ----- | ---------------------------------------------- |
| 1.4.1 | 组装函数：问题 + 检索片段 + 文件结构摘要 → 结构化 prompt | query + chunks + repo map | `context_assembler.py` | 1.3.2 | Token 预算控制：不超模型窗口；代码片段格式保持 |
| 1.4.2 | Repo Map 生成：快速生成项目文件树 + 关键符号摘要         | 仓库根路径                | 轻量级仓库地图文本     | 1.1.3 | 大仓库（1000+文件）的地图压缩策略              |

---

### 阶段 2：知识图谱层（2-3 天）

**目标**：构建符号-调用关系图谱，支持结构化查询。

> **ponytail 提醒**：若仅需 F1-F7 功能，向量检索+Repo Map 已足够。知识图谱增量价值在于 F2（补全）和 F3（重构）的依赖分析。若时间紧，可降级为内存中的简单调用图（networkx），Neo4j 引入是可选迁移路径。

| #   | 任务                                                        | 输入                 | 输出                                        | 依赖  | 难点                                                           |
| --- | ----------------------------------------------------------- | -------------------- | ------------------------------------------- | ----- | -------------------------------------------------------------- |
| 2.1 | 符号提取：从 AST 提取函数/类/方法定义 + 调用关系            | AST 节点树           | `(symbol_nodes, call_edges)` 列表           | 1.1.1 | 跨文件调用解析（import 溯源）；动态调用（getattr）无法静态分析 |
| 2.2 | 内存图谱构建：用 networkx 建图 + 基本查询（入度/出度/路径） | nodes + edges        | `knowledge_graph/builder.py` + `querier.py` | 2.1   | 大规模仓库的图大小控制                                         |
| 2.3 | LLM 语义摘要：对关键符号生成自然语言描述摘要                | 函数签名 + docstring | 符号维度的语义摘要（可选存为向量）          | 2.2   | LLM 调用成本和时间                                             |
| 2.4 | 影响面分析：查询 "修改函数 X 会影响哪些调用链"              | graph + query        | 影响面路径                                  | 2.2   | 间接调用链的深度控制                                           |
| 2.5 | （可选）Neo4j/Memgraph 持久化                               | 内存图               | 数据库图                                    | 2.2   | 需要额外基础设施；ponytail: 先跳过，内存 networkx 够用         |

---

### 阶段 3：Deep Agents 智能体编排（2-3 天）

**目标**：将 RAG 管道注册为 Agent Tool，配置完整的 Deep Agents Harness。

#### 3.1 RAG Tool 注册

| #     | 任务                                                | 输入               | 输出                    | 依赖     | 难点                                                     |
| ----- | --------------------------------------------------- | ------------------ | ----------------------- | -------- | -------------------------------------------------------- |
| 3.1.1 | `rag_search` Tool：接收 query，返回相关代码片段     | RAG pipeline       | `tools/rag_search.py`   | 1.4      | Tool description 需精准描述能力边界，便于 Agent 正确路由 |
| 3.1.2 | `rag_ask` Tool：接收问题，返回基于 RAG 上下文的回答 | pipeline + LLM     | `tools/rag_ask.py`      | 1.4      | 区分 search（返回片段）和 ask（返回回答）的语义          |
| 3.1.3 | `graph_query` Tool：知识图谱查询（依赖链、影响面）  | knowledge_graph    | `tools/graph_query.py`  | 2.2      | 查询类型枚举 vs 自由格式的权衡                           |
| 3.1.4 | `code_analyze` Tool：针对特定文件/函数的深度分析    | AST + graph + RAG  | `tools/code_analyze.py` | 2.2, 1.3 | 分析结果的结构化输出格式                                 |
| 3.1.5 | `doc_generate` Tool：为指定符号生成文档             | code context + LLM | `tools/doc_generate.py` | 1.3      | 文档风格一致性                                           |

#### 3.2 智能体装配

| #     | 任务                                                 | 输入             | 输出                        | 依赖  | 难点                                    |
| ----- | ---------------------------------------------------- | ---------------- | --------------------------- | ----- | --------------------------------------- |
| 3.2.1 | `create_deeprag_agent()` 工厂：组装所有参数          | 所有 Tool + 配置 | `agent/factory.py`          | 3.1   | 参数过多时的默认值设计                  |
| 3.2.2 | 系统提示词：编码专家角色 + 仓库专家行为规范          | 需求             | `agent/prompts.py`          | —     | 提示词长度 vs 有效性的平衡              |
| 3.2.3 | Harness Profiles：针对不同模型调优配置               | 模型特性         | `agent/profiles.py`         | —     | 需要实测不同模型的表现差异              |
| 3.2.4 | 子智能体定义：code-analyzer、doc-generator、refactor | 场景             | `agent/subagents.py`        | 3.2.1 | 子智能体的 tool 和 skill 分配           |
| 3.2.5 | 权限规则：保护代码仓库不被误写                       | 安全需求         | `agent/permissions.py`      | 3.2.1 | 读写粒度（allow 白名单 vs deny 黑名单） |
| 3.2.6 | 记忆配置：AGENTS.md 注入 + CompositeBackend 长记忆   | 需求             | `memory/project_context.py` | 3.2.1 | 跨会话项目知识的累积策略                |

---

### 阶段 4：Skills 技能包（1-2 天）

**目标**：按 Agent Skills 规范编写领域专用 Skills。

| #   | 任务                                                | 输入     | 输出                                       | 依赖  | 难点                                                  |
| --- | --------------------------------------------------- | -------- | ------------------------------------------ | ----- | ----------------------------------------------------- |
| 4.1 | `code-review` Skill：评审检查清单、反模式、安全规则 | 最佳实践 | `skills/code-review/SKILL.md` + references | 3.2   | 规则覆盖面与长度的权衡（Progressive Disclosure 控制） |
| 4.2 | `refactor` Skill：重构策略、依赖分析步骤、安全验证  | 重构模式 | `skills/refactor/SKILL.md` + references    | 2.4   | 不同语言的重构差异                                    |
| 4.3 | `doc-gen` Skill：文档模板、风格指南、类型提示       | 文档规范 | `skills/doc-gen/SKILL.md` + references     | 3.1.5 | 多语言文档格式差异                                    |
| 4.4 | `bug-hunt` Skill：常见 Bug 模式、排查流程、修复模板 | Bug 案例 | `skills/bug-hunt/SKILL.md` + references    | —     | 需要积累实际案例                                      |

---

### 阶段 5：CLI 入口（1 天）

**目标**：提供 `deeprag-coder` 命令行工具。

| #   | 任务                                      | 输入          | 输出                      | 依赖     | 难点                              |
| --- | ----------------------------------------- | ------------- | ------------------------- | -------- | --------------------------------- |
| 5.1 | `deeprag-coder init --repo ./my-project`  | RAG pipeline  | Typer CLI：初始化仓库索引 | 1.4, 2.2 | 长时间初始化的进度反馈            |
| 5.2 | `deeprag-coder ask "JWT 验证在哪里？"`    | agent         | CLI 交互式问答            | 3.2      | 流式输出的终端展示                |
| 5.3 | `deeprag-coder review --file src/auth.py` | agent + skill | CLI 单文件评审            | 3.2, 4.1 | 评审结果的格式化渲染（Rich 面板） |
| 5.4 | `deeprag-coder interactive`               | agent         | 交互式 REPL 会话          | 3.2      | 多轮对话的状态管理                |

---

### 阶段 6：测试与文档（1-2 天）

| #   | 任务                                         | 输入     | 输出                | 依赖 |
| --- | -------------------------------------------- | -------- | ------------------- | ---- |
| 6.1 | RAG 管道单元测试：分块完整性、检索准确率     | 各模块   | `tests/test_rag/`   | 1-2  |
| 6.2 | Tool 集成测试：Agent 调用 Tool 的正确性      | Agent    | `tests/test_tools/` | 3    |
| 6.3 | 端到端场景测试：代码问答、Bug 定位、文档生成 | 真实仓库 | `tests/test_e2e/`   | 3-5  |
| 6.4 | 使用文档：安装说明、CLI 命令、Python API     | 全部     | docs/               | 5    |

---

## 四、逐条功能覆盖说明

| README 功能           | 实现方式                                                                                         | 对应模块/阶段                      |
| --------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------- |
| **F1 代码问答**       | `rag_search` + `rag_ask` Tool → Agent 接收自然语言问题 → 检索相关代码 → LLM 综合回答             | 3.1.1, 3.1.2                       |
| **F2 智能代码补全**   | `rag_search` 检索上下文 + Repo Map 全局结构 → Agent 基于完整上下文生成补全                       | 1.4.2, 3.1.1                       |
| **F3 跨文件重构**     | `graph_query` 查依赖链路 + `rag_search` 查所有引用点 → `refactor` Skill 指导步骤 → Agent 执行    | 2.4, 3.1.3, 4.2                    |
| **F4 代码审查**       | `code-review` Skill 加载评审规则 → `rag_search` 获取相关代码 → Agent 逐条审查                    | 4.1                                |
| **F5 文档生成**       | `doc_generate` Tool → LLM 基于代码上下文生成 → `doc-gen` Skill 保证风格一致                      | 3.1.5, 4.3                         |
| **F6 Bug 定位与修复** | `rag_search` 语义定位 → `bug-hunt` Skill 匹配 Bug 模式 → Agent 分析根因并生成修复                | 4.4                                |
| **F7 新手上手**       | Repo Map 提供全局视图 + `rag_ask` 回答导航问题                                                   | 1.4.2, 3.1.2                       |
| **F8 任务规划与委派** | Deep Agents 原生：`TodoListMiddleware` + `SubAgentMiddleware` → 主智能体 write_todos → task 委派 | 框架原生                           |
| **F9 虚拟文件系统**   | Deep Agents 原生：`FilesystemMiddleware` → ls/read/write/edit/grep/glob                          | 框架原生                           |
| **F10 上下文管理**    | Deep Agents 原生：`SummarizationMiddleware` → 85% 窗口自动压缩                                   | 框架原生                           |
| **F11 持久化记忆**    | Deep Agents 原生：`CompositeBackend` + `StoreBackend` → `/memories/` 跨会话                      | 框架原生                           |
| **F12 人机协作**      | Deep Agents 原生：`interrupt_on` 配置 → `HumanInTheLoopMiddleware`                               | 框架原生                           |
| **F13 Skills 技能**   | Deep Agents 原生：`SkillsMiddleware` + Progressive Disclosure → 按需加载 SKILL.md                | 框架原生（阶段 4 编写 Skill 内容） |
| **F14 MCP 支持**      | Deep Agents 原生：框架支持 MCP Tool 注册                                                         | 框架原生                           |
| **F15 代码解释器**    | Deep Agents 原生：`CodeInterpreterMiddleware(backend)` + quickjs                                 | 框架原生                           |

**本项目需构建的部分 = F16-F19（RAG 管道）+ F1-F7 中 Agent 侧的 Tool/Skill 编排（RAG+KG 的对外接口）。** Deep Agents 框架直接覆盖了基础设施（F8-F15），开发重心在"代码专用 RAG 检索"这个差异化能力上。

---

## 五、需要扩展或定制的部分

| Deep Agents 默认行为           | 本项目定制需求                                   | 方案                                                                                    |
| ------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------------------------- |
| **默认工具集**（文件+todo）    | 追加 5 个 RAG/KG Tool 和 4 个 Skill              | `tools=[rag_search, rag_ask, graph_query, code_analyze, doc_generate]` + `skills=[...]` |
| **默认系统提示词**（通用助手） | 定制为"代码仓库专家 + 编码助手"角色              | `system_prompt=CODE_REPO_EXPERT_PROMPT`                                                 |
| **默认 StateBackend**          | 需要操作真实代码仓库文件 → FilesystemBackend     | `backend=FilesystemBackend(root_dir=repo_path, virtual_mode=True)`                      |
| **默认无子智能体**             | 功能拆分：analyzer/doc-gen/refactor 专用子智能体 | `subagents=[analyzer_sub, doc_sub, refactor_sub]`                                       |
| **默认 Memory**                | 注入项目 AGENTS.md + 积累跨会话仓库知识          | `memory=["AGENTS.md"]` + `CompositeBackend` + `/memories/`                              |
| **默认无 interrupt_on**        | 写操作需要审批（保护仓库）                       | `interrupt_on={"write_file": True, "edit_file": True}`                                  |
| **HarnessProfile**             | 针对编码场景微调压缩阈值和通用子智能体行为       | `profile=HarnessProfile(...)`                                                           |
| **异步子智能体**               | 大型仓库的分析任务适合异步执行                   | `AsyncSubAgent(name="deep-analyzer", ...)`                                              |

---

## 六、风险与缓解

| 风险                                       | 影响阶段 | 缓解策略                                               |
| ------------------------------------------ | -------- | ------------------------------------------------------ |
| Tree-sitter 多语言 parser 编译/安装复杂    | 1.1      | 先只支持 Python + TS + JS（覆盖面 80%+），后续按需扩展 |
| 向量检索准确率达不到 85%+                  | 1.3      | 预埋实验对比脚本；混合检索权重可调参；重排序兜底       |
| 大仓库（10000+ 文件）的 RAG 初始化耗时过长 | 1.2.1    | 增量更新 + 分批嵌入 + 跳过无关目录                     |
| 知识图谱的内存占用爆炸                     | 2        | ponytail：先用 networkx 内存图，仅存关键符号边         |
| 不同 LLM 对 Tool 调用的路由准确性差异      | 3        | HarnessProfile 按模型微调；Tool description 清晰防歧义 |
