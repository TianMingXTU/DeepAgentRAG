"""DeepRAG-Coder Agent 入口 — 演示完整编排能力。"""

import logging

from deeprag_coder.agent.factory import create_deeprag_agent
from deeprag_coder.rag.pipeline import init_rag

logger = logging.getLogger(__name__)


def main():
    logger.info("初始化 RAG 索引")
    n = init_rag()
    logger.info("索引完成: %d chunks", n)

    agent = create_deeprag_agent()

    questions = [
        "这个项目的核心架构是什么？",
        "搜索代码中关于 RAG 管道的实现",
    ]

    for q in questions:
        logger.info("用户: %s", q)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": q}]}
        )
        logger.info("回答: %s", result["messages"][-1].content)


if __name__ == "__main__":
    main()
