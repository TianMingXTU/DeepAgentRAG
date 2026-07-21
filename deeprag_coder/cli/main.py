"""CLI 入口 — Typer 命令行工具。
 
 用法:
     dc init                  # 索引当前仓库
     dc ask "问题"            # 单次问答
     dc review --file src/a.py # 单文件代码评审
     dc interactive           # 交互式 REPL
"""
 
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
def review(
    file: str = typer.Option(..., "--file", "-f", help="要审查的文件路径"),
) -> None:
    """对单个代码文件进行 AI 代码评审。"""
    init_rag()
    pipe = get_pipeline()
    docs = pipe.search(f"review {file}", top_k=5)
    repo_map = generate_repo_map(pipe.repo_path, max_files=20)
    context = "\n---\n".join(
        f"{d.metadata.get('file_path', '?')}:\n{d.page_content}" for d in docs
    )
    prompt = (
        f"Review the code file `{file}` for correctness, security, performance, "
        f"and style. Output a structured review with severity, line numbers, "
        f"and suggestions.\n\n"
        f"## Project Structure\n{repo_map}\n\n"
        f"## Code Context\n{context}"
    )
    agent = create_deeprag_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    md = Markdown(result["messages"][-1].content)
    console.print(Panel(md, title=f"代码评审: {file}", border_style="yellow"))


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
