"""CLI 入口 — Typer 命令行工具。

用法:
    dc init                  # 索引当前仓库
    dc ask "问题"            # 单次问答
    dc interactive           # 交互式 REPL
"""

import typer
from rich.console import Console
from rich.panel import Panel

from deeprag_coder.agent.factory import create_deeprag_agent
from deeprag_coder.rag.pipeline import init_rag

app = typer.Typer()
console = Console()


@app.command()
def init(
    repo: str = typer.Option(".", "--repo", "-r", help="仓库根路径"),
) -> None:
    """初始化仓库索引（分块 → 嵌入 → 向量库 → BM25 → 知识图谱）。"""
    with console.status("[bold green]索引中..."):
        n = init_rag(repo)
    console.print(f"[green]索引完成: {n} chunks[/green]")


@app.command()
def ask(
    question: str = typer.Argument(..., help="关于代码库的问题"),
) -> None:
    """单次问答：检索 + LLM 回答。"""
    init_rag()
    agent = create_deeprag_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    console.print(Panel(result["messages"][-1].content, title="回答"))


@app.command()
def interactive() -> None:
    """交互式 REPL 会话（多轮对话）。"""
    init_rag()
    agent = create_deeprag_agent()
    messages: list[dict] = []
    console.print("[bold]DeepRAG-Coder REPL (输入 exit 退出)[/bold]")

    while True:
        try:
            q = console.input("\n[bold cyan]> [/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("exit", "quit"):
            break

        messages.append({"role": "user", "content": q})
        result = agent.invoke({"messages": messages})
        reply = result["messages"][-1].content
        console.print(Panel(reply, title="回答"))
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    app()
