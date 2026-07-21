# DeepRAG-Coder v2 改进计划

> **核心框架**：**LangChain Deep Agents** (deepagents≥0.6.12) + **LangChain** + **LangGraph**  
> **核心原则**：最小化改动 —— 只在现有架构无法满足时才引入新模块，优先复用/配置框架原生能力。

---

## 一、现状差距分析（基于 Deep Agents / LangChain / LangGraph 能力对标）

| 维度 | DeepAgentRAG v1 现状 | OpenCode/Codex/Claude Code 优势 | Deep Agents / LangGraph 原生能力 | 改进优先级 |
|------|---------------------|--------------------------------|----------------------------------|-----------|
| **交互模式** | 纯 CLI + 单一 REPL | TUI 多标签、Tab 切换 Agent、@mention 子智能体 | `create_deep_agent` 支持多 Agent 实例、Subagent 委派 | P1 |
| **Agent 体系** | 3 个固定子智能体 | Primary/Subagent 分层、Plan/Build 双模式、隐藏系统 Agent | `subagents` 参数、`interrupt_on`、`HumanInTheLoopMiddleware` | P1 |
| **权限控制** | 仅写保护 3 个目录 | 细粒度 glob 权限、ask/allow/deny 三态、bash 命令级控制 | `FilesystemPermission` + 自定义 Permission 扩展 | P0 |
| **配置系统** | 硬编码 dataclass + .env | JSONC 分层配置、远程/全局/项目/环境变量优先级、Schema 校验 | LangChain `RunnableConfig` + 可序列化配置 | P0 |
| **记忆/上下文** | InMemoryStore + AGENTS.md | Snapshot/Undo、Compaction 自动压缩、多层 Memory | `CompositeBackend` + `StoreBackend` + `SummarizationMiddleware` | P1 |
| **代码智能** | 纯 RAG/ KG (tree-sitter) | LSP 集成、定义跳转、引用查找、MCP 协议 | LangChain Tool + 自定义 LSP Tool | P1 |
| **技能系统** | 4 个目录级 Skill | Markdown 技能文件、Progressive Disclosure、版本化 | `SkillsMiddleware` + `Skill` 规范 | P2 |
| **多会话** | 单会话 REPL | 会话分享链接、子会话导航、标题/摘要自动生成 | LangGraph `checkpointer` + `MemorySaver`/`PostgresSaver` | P2 |

---

## 二、v2 目标：仅做 6 项最小化增强（全部基于 Deep Agents / LangChain / LangGraph 原生扩展）

### 1. Plan/Build 双模式 Agent（复用 Deep Agents `interrupt_on` + `permissions`）
- **现有**：单一 `create_deeprag_agent()`，写操作统一 `interrupt_on={"write_file": True, "edit_file": True}`
- **改进**：`factory.py` 增加 `mode: Literal["plan", "build"]` 参数
  - `plan`：`interrupt_on={}` + 只读权限（`read/glob/grep/lsp` 允许，其余 deny）
  - `build`：完整权限 + `interrupt_on` 审批
- **框架复用**：Deep Agents `create_deep_agent(interrupt_on=..., permissions=...)` 原生支持
- **改动**：`agent/factory.py` +30 行，`cli/main.py` 新增 `/plan` `/build` 子命令

### 2. 细粒度权限系统（扩展 Deep Agents `FilesystemPermission`）
- **现有**：仅 `DENY_SELF_WRITE` / `DENY_ENV_WRITE` / `DENY_GIT_WRITE` 三条 `FilesystemPermission`
- **改进**：新增 `PermissionRule(tool: str, pattern: str, action: Literal["allow","ask","deny"])` 数据类
  - `tool` 覆盖：`read|edit|write|glob|grep|bash|task|lsp|webfetch|...`
  - `pattern` 支持 glob：`**/*.py`、`git push*`、`rm -rf *`
  - `action` 三态：OpenCode/Codex 风格（默认 allow）或 Claude Code 风格（默认 ask）
- **框架复用**：Deep Agents `FilesystemPermission` 仅管文件系统，我们在 `factory.py` 组装完整权限矩阵传给 `create_deep_agent(permissions=...)`
- **改动**：`agent/permissions.py` 重写，`factory.py` 调用新规则构建器

### 3. 分层配置系统（LangChain `RunnableConfig` + JSON Schema 校验）
- **现有**：`settings.py` 硬编码 dataclass + `.env` 单层
- **改进**：新增 `config/loader.py` 实现 4 层合并（优先级低→高）
  1. **Remote**（组织级 `.well-known/deeprag`，预留）
  2. **Global** `~/.config/deeprag/deeprag.json`
  3. **Project** `./deeprag.json`（可提交 Git）
  4. **Env** 环境变量（最高，兼容现有 `.env`）
- **Schema**：`config/schema.json`（JSON Schema Draft 2020-12），IDE 自动补全
- **框架复用**：LangChain `RunnableConfig` 标准化配置传递；`settings.py` 保留为默认值回退工厂
- **改动**：新增 `config/loader.py` `config/schema.json`，`settings.py` 迁移为从 loader 读取

### 4. 子智能体 @mention 机制（复用 Deep Agents `Task` tool + Subagent 委派）
- **现有**：3 个固定 `subagents=[...]`，仅由主 Agent 自动调度
- **改进**：
  - `prompts.py` 系统提示词注入 `@code-analyzer @doc-generator @refactor` 用法说明
  - `factory.py` 确保 `subagents` 列表每个 dict 含 `name` 字段，Deep Agents 自动暴露给 `Task` tool
  - 用户在 REPL 中输入 `@code-analyzer explain auth.py` → 主 Agent 调用 `Task` tool 委派
- **框架复用**：Deep Agents `create_deep_agent(subagents=[...])` 原生支持 `@name` 调用
- **改动**：`agent/prompts.py` +10 行，`agent/factory.py` 验证 name 暴露

### 5. Snapshot/Undo + 自动 Compaction（复用 Deep Agents Middleware）
- **现有**：无撤销，上下文无压缩
- **改进**：
  - `FilesystemBackend(snapshot=True)` 开启文件快照（LangGraph `BaseCheckpointSaver` 兼容）
  - `create_deep_agent(compaction={"auto": True, "reserved_tokens": 8000})` 启用 `SummarizationMiddleware`
  - CLI 新增 `/undo` `/redo` 命令调用 `backend.snapshot.undo()/redo()`
- **框架复用**：Deep Agents `FilesystemBackend` 内置 snapshot，`SummarizationMiddleware` 原生 compaction
- **改动**：`agent/factory.py` 仅增 2 个参数，`cli/main.py` +3 个命令

### 6. LSP 集成最小化（LangChain Tool 封装 pyright / 通用 LSP 客户端）
- **现有**：纯 AST 静态分析（tree-sitter），无跨文件跳转
- **改进**：新增 `tools/lsp_tool.py` 两个 `@tool`
  - `lsp_goto_def(symbol: str, file: str) -> dict`：调用 `pyright --outputjson` 或 `pylsp` 解析定义位置
  - `lsp_references(symbol: str, file: str) -> list[dict]`：查找所有引用
  - 降级策略：pyright 未安装 → 回退 tree-sitter 符号搜索
- **框架复用**：LangChain `@tool` 标准化，直接加入 `factory.py` tools 列表
- **改动**：新增 1 文件 `tools/lsp_tool.py`，`factory.py` tools +2

---

## 三、分阶段实施计划（共 5 天，仅新增/修改 10 个文件）

| 阶段 | 任务 | 产出文件 | 预估工时 | 依赖 |
|------|------|----------|----------|------|
| **P0-权限与配置** | 1.1 重写 `permissions.py` 支持 glob pattern + ask/allow/deny | `agent/permissions.py` | 0.5 天 | — |
| | 1.2 新增 `config/loader.py` + `schema.json`，4 层合并 | `config/loader.py` `config/schema.json` | 0.5 天 | 1.1 |
| | 1.3 `settings.py` 迁移为 loader 读取，保留默认值 | `config/settings.py` | 0.5 天 | 1.2 |
| **P1-双模式 Agent** | 2.1 `factory.py` 增加 `mode` 参数创建 Plan/Build Agent | `agent/factory.py` | 0.5 天 | P0 完成 |
| | 2.2 `cli/main.py` 新增 `/plan` `/build` 子命令 | `cli/main.py` | 0.5 天 | 2.1 |
| **P1-子 Agent @mention** | 3.1 更新 `prompts.py` 注入 @mention 用法 | `agent/prompts.py` | 0.25 天 | 2.1 |
| | 3.2 验证 subagent name 暴露给 Task tool | `agent/factory.py` | 0.25 天 | 3.1 |
| **P1-Snapshot/Compaction** | 4.1 `factory.py` 启用 snapshot + compaction 参数 | `agent/factory.py` | 0.25 天 | 2.1 |
| **P1-LSP 工具** | 5.1 新增 `tools/lsp_tool.py`（pyright JSON 解析 + 降级） | `tools/lsp_tool.py` | 0.5 天 | — |
| | 5.2 注册到 `factory.py` tools 列表 | `agent/factory.py` | 0.25 天 | 5.1 |
| **P2-技能与会话增强** | 6.1 Skills 目录改为 Markdown + frontmatter（兼容现有） | `skills/*/SKILL.md` | 0.5 天 | — |
| | 6.2 `cli/main.py` 新增 `/undo` `/redo` `/share` 命令 | `cli/main.py` | 0.5 天 | 4.1 |

**总计：约 5 天，核心逻辑复用 Deep Agents / LangChain / LangGraph 90%+**

---

## 四、关键代码变更草案（框架集成点）

### 4.1 `agent/permissions.py` —— 扩展 Deep Agents `FilesystemPermission`
```python
from dataclasses import dataclass
from typing import Literal
from deepagents import FilesystemPermission

@dataclass(frozen=True)
class PermissionRule:
    """细粒度权限规则，覆盖所有 Tool 类别"""
    tool: str                    # "read" | "edit" | "write" | "glob" | "grep" | "bash" | "task" | "lsp" | "webfetch" | ...
    pattern: str                 # glob pattern: "**/*.py" | "git push*" | "rm -rf *"
    action: Literal["allow", "ask", "deny"]  # 三态

# 默认规则：保护自身源码 + 敏感文件 + 危险命令，其余默认 allow（OpenCode 风格）
DEFAULT_RULES: tuple[PermissionRule, ...] = (
    PermissionRule("edit", "**/deeprag_coder/**", "deny"),
    PermissionRule("write", "**/deeprag_coder/**", "deny"),
    PermissionRule("edit", ".env*", "deny"),
    PermissionRule("write", ".env*", "deny"),
    PermissionRule("edit", ".git/**", "deny"),
    PermissionRule("bash", "rm -rf *", "deny"),
    PermissionRule("bash", "git push --force*", "ask"),
)

def build_deepagents_permissions(rules: tuple[PermissionRule, ...], mode: str = "build") -> list[FilesystemPermission]:
    """将 PermissionRule 转换为 Deep Agents 接受的 FilesystemPermission 列表"""
    # 仅文件系统类工具走 FilesystemPermission；bash/task/lsp 等由框架内部权限矩阵处理
    fs_rules = [r for r in rules if r.tool in ("read", "edit", "write", "glob", "grep")]
    if mode == "plan":
        fs_rules = [r for r in fs_rules if r.tool in ("read", "glob", "grep")]
    return [
        FilesystemPermission(operations=[r.tool], paths=[r.pattern], mode=r.action)
        for r in fs_rules
    ]
```

### 4.2 `config/loader.py` —— LangChain `RunnableConfig` 兼容的分层加载
```python
import json
from pathlib import Path
from deeprag_coder.config.settings import Settings

CONFIG_PATHS = [
    Path("~/.config/deeprag/deeprag.json").expanduser(),  # Global
    Path.cwd() / "deeprag.json",                          # Project
]

def load_config() -> Settings:
    """4 层合并：Defaults → Global → Project → Env（Env 在 Settings.__post_init__ 处理）"""
    base = Settings()  # 默认值工厂
    for p in CONFIG_PATHS:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            base = _merge_dataclass(base, data)
    return base

def _merge_dataclass(obj: Settings, data: dict) -> Settings:
    """浅合并 dataclass 字段，嵌套 dataclass 递归合并"""
    from dataclasses import fields, is_dataclass, replace
    updates = {}
    for f in fields(obj):
        if f.name in data:
            val = data[f.name]
            if is_dataclass(f.type) and isinstance(val, dict):
                updates[f.name] = _merge_dataclass(getattr(obj, f.name), val)
            else:
                updates[f.name] = val
    return replace(obj, **updates)
```

### 4.3 `agent/factory.py` —— Deep Agents `create_deep_agent` 统一装配入口
```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI

from deeprag_coder.config.loader import load_config
from deeprag_coder.agent.permissions import build_deepagents_permissions, DEFAULT_RULES
from deeprag_coder.agent.prompts import CODE_REPO_EXPERT_PROMPT
from deeprag_coder.agent.subagents import (
    code_analyzer_subagent,
    doc_generator_subagent,
    refactor_subagent,
)
from deeprag_coder.memory.project_context import create_memory_backend, get_store, MemoryContext
from deeprag_coder.tools.rag_search import rag_search
from deeprag_coder.tools.rag_ask import rag_ask
from deeprag_coder.tools.graph_query import graph_query
from deeprag_coder.tools.code_analyze import code_analyze
from deeprag_coder.tools.doc_generate import doc_generate
from deeprag_coder.tools.lsp_tool import lsp_goto_def, lsp_references  # 新增

def create_deeprag_agent(
    repo_path: str | None = None,
    mode: Literal["plan", "build"] = "build",
) -> object:
    """
    创建装配完整的 DeepRAG-Coder Agent。
    
    Args:
        repo_path: 仓库根路径，None 时从配置读取
        mode: "plan" 只读分析模式 | "build" 读写执行模式（需审批）
    """
    cfg = load_config()
    llm = ChatOpenAI(
        model=cfg.llm.model,
        api_key=cfg.llm.api_key,
        base_url=cfg.llm.base_url,
        temperature=0,
    )
    root = repo_path or str(cfg.repo_path)

    # 统一工具集：RAG + KG + LSP
    tools = [
        rag_search, rag_ask, graph_query, code_analyze, doc_generate,
        lsp_goto_def, lsp_references,  # 新增 LSP 工具
    ]

    # 子智能体：name 字段必须存在，供 @mention / Task tool 识别
    subagents = [
        code_analyzer_subagent,
        doc_generator_subagent,
        refactor_subagent,
    ]

    # Skills 目录（Deep Agents SkillsMiddleware 自动加载）
    skills = [
        "deeprag_coder/skills/code-review/",
        "deeprag_coder/skills/refactor/",
        "deeprag_coder/skills/doc-gen/",
        "deeprag_coder/skills/bug-hunt/",
    ]

    # 权限矩阵
    permissions = build_deepagents_permissions(DEFAULT_RULES, mode=mode)

    # 记忆后端：CompositeBackend(StateBackend + StoreBackend)
    backend = create_memory_backend()
    store = get_store()

    # 文件系统后端：启用 Snapshot（Undo/Redo）
    fs_backend = FilesystemBackend(
        root_dir=root,
        virtual_mode=True,
        snapshot=True,  # 关键：开启快照
    )

    return create_deep_agent(
        model=llm,
        system_prompt=CODE_REPO_EXPERT_PROMPT,
        tools=tools,
        subagents=subagents,
        skills=skills,
        backend=fs_backend,           # 替换默认 backend
        store=store,
        permissions=permissions,
        memory=["/memories/AGENTS.md"],
        context_schema=MemoryContext,
        interrupt_on={
            "write_file": {"allowed_decisions": ["approve", "edit", "reject"]},
            "edit_file": {"allowed_decisions": ["approve", "edit", "reject"]},
        } if mode == "build" else {},  # Plan 模式零中断
        compaction={"auto": True, "reserved_tokens": 8000},  # SummarizationMiddleware
    )
```

### 4.4 `cli/main.py` —— Plan/Build 切换 + Undo/Redo + @mention 提示
```python
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from deeprag_coder.agent.factory import create_deeprag_agent
from deeprag_coder.rag.pipeline import init_rag, get_pipeline
from deeprag_coder.utils.repo_map import generate_repo_map

app = typer.Typer()
console = Console()

@app.command()
def init(repo: str = typer.Option(".", "--repo", "-r", help="仓库根路径")):
    """初始化仓库索引（分块 → 嵌入 → 向量库 → BM25 → 知识图谱）"""
    with console.status("[bold green]索引中..."):
        n = init_rag(repo)
    console.print(f"[green]索引完成: {n} chunks[/green]")

@app.command()
def plan(question: str = typer.Argument(None, help="只读分析问题")):
    """Plan 模式：只读分析，不修改代码（零 interrupt_on）"""
    init_rag()
    agent = create_deeprag_agent(mode="plan")
    q = question or console.input("[bold cyan]Plan> [/bold cyan]")
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    console.print(Panel(result["messages"][-1].content, title="Plan 回答", border_style="blue"))

@app.command()
def build(question: str = typer.Argument(None, help="读写执行问题")):
    """Build 模式：可读可写，写操作需审批"""
    init_rag()
    agent = create_deeprag_agent(mode="build")
    q = question or console.input("[bold green]Build> [/bold green]")
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    console.print(Panel(result["messages"][-1].content, title="Build 回答", border_style="green"))

@app.command()
def interactive():
    """交互式 REPL：支持 /plan /build /undo /redo 内部命令"""
    init_rag()
    agent = create_deeprag_agent(mode="build")
    messages: list[dict] = []
    mode = "build"
    console.print("[bold]DeepRAG-Coder REPL[/bold] — 命令: [cyan]/plan[/cyan] [green]/build[/green] [yellow]/undo[/yellow] [yellow]/redo[/yellow] [magenta]/share[/magenta] [red]exit[/red]")

    while True:
        try:
            prompt = f"[bold {'cyan' if mode=='plan' else 'green'}]{mode}> [/bold {'cyan' if mode=='plan' else 'green'}]"
            q = console.input(prompt)
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("exit", "quit"):
            break
        if q == "/plan":
            agent = create_deeprag_agent(mode="plan")
            mode = "plan"
            console.print("[cyan]Switched to PLAN mode (read-only)[/cyan]")
            continue
        if q == "/build":
            agent = create_deeprag_agent(mode="build")
            mode = "build"
            console.print("[green]Switched to BUILD mode (read-write)[/green]")
            continue
        if q == "/undo":
            # 调用 backend.snapshot.undo() —— 需要暴露 backend 引用
            console.print("[yellow]Undo not yet wired to backend.snapshot[/yellow]")
            continue
        if q == "/redo":
            console.print("[yellow]Redo not yet wired[/yellow]")
            continue

        messages.append({"role": "user", "content": q})
        result = agent.invoke({"messages": messages})
        reply = result["messages"][-1].content
        console.print(Panel(reply, title="回答"))
        messages.append({"role": "assistant", "content": reply})

# 其余 review/ask 等命令保持不变...
```

---

## 五、验收标准（框架能力视角）

| 指标 | v1 现状 | v2 目标 | 验收方式 | 框架对应能力 |
|------|---------|---------|----------|--------------|
| 权限误写源码 | 否（硬编码 deny） | 否（glob pattern 可配置） | `dc init && echo "x" > deeprag_coder/x.py` → 被拦截 | `FilesystemPermission` + 自定义规则 |
| Plan 模式零写入 | 无 | 是 | `dc plan "analyze auth"` → 无文件变更 | `interrupt_on={}` + 只读权限 |
| 配置分层生效 | 否 | 是 | 全局 `model=sonnet`，项目 `model=haiku` → 生效 haiku | `RunnableConfig` 兼容加载器 |
| @mention 子 Agent | 否 | 是 | `@code-analyzer explain auth.py` → 触发 Task tool 委派 | `subagents` + `Task` tool |
| Undo 撤销 | 无 | 支持 5 步 | 编辑文件 → `/undo` → 文件恢复 | `FilesystemBackend(snapshot=True)` |
| LSP 跳转定义 | 无 | pyright 支持 | `lsp_goto_def("AuthService.login")` → 文件:行号 | LangChain `@tool` 封装 |
| 自动 Compaction | 无 | 8k token 预留自动摘要 | 长对话自动触发摘要压缩 | `SummarizationMiddleware` |

---

## 六、不做的事（YAGNI —— 避免过度工程）

1. **TUI 重写** — 现有 Rich CLI 足够，Tab 切换用键盘监听即可；Deep Agents 原生 Web/IDE 由 OpenCode 覆盖
2. **MCP 服务器** — Deep Agents 原生支持 `mcp` 参数，按需接入
3. **Neo4j 知识图谱** — 现有 `networkx` 内存图足够，规模 >10k 文件再迁移
4. **多模型路由** — 先用单模型，`HarnessProfile` 调优即可
5. **Web/IDE 扩展** — CLI 优先，桌面端由 OpenCode 生态覆盖

---

## 七、风险与缓解（框架版本锁定）

| 风险 | 影响 | 缓解 |
|------|------|------|
| Deep Agents 版本升级破坏 `create_deep_agent` 签名 | P0 | `pyproject.toml` 锁定 `deepagents>=0.6.12,<0.7`，CI 跑集成测试 |
| 权限系统过严导致 Agent 无法工作 | P1 | 默认 `allow`，仅保护核心目录；提供 `--permission-debug` 旁路 |
| LSP 依赖 pyright 未安装 | P2 | `lsp_tool.py` 捕获 `FileNotFoundError` 降级为 tree-sitter 搜索 |
| 配置合并优先级错误 | P1 | 单元测试覆盖 4 层合并场景（`tests/test_config_loader.py`） |

---

## 八、后续迭代（v2.1+，基于框架路线图）

- **Skills 版本化**：`SKILL.md` 增加 `version` 字段，支持 `@skill-name@v1.2`
- **会话分享链接**：复用 Deep Agents `share` middleware，生成只读 URL
- **后台任务调度**：`/schedule "daily code review"` → 结合 LangGraph `cron` 节点
- **企业级 RBAC**：接入 `config/loader.py` 的 remote config 层
- **LangGraph Platform 部署**：`langgraph-server` + `langgraph-checkpoint-postgres` 生产化

---

## 执行原则（Ponytail 模式）

> 每次 PR 只改 1-2 个文件，跑通 `uv run pytest tests/ -v` 后再提交。  
> 先做 P0/P1（权限、配置、双模式、LSP、Snapshot），P2 留作增量。  
> **优先复用 Deep Agents / LangChain / LangGraph 原生能力，只写胶水代码。**