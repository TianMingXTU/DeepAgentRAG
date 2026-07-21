"""DeepRAG-Coder Agent 入口。"""

from deeprag_coder.agent.factory import create_deeprag_agent
from deeprag_coder.rag.pipeline import init_rag


def main():
    # 1. 初始化
    n = init_rag()
    print(f"索引完成: {n} chunks")

    # 2. 启动 Agent
    agent = create_deeprag_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "这个项目的核心架构是什么？"}]}
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
