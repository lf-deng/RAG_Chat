import inspect
import os
import asyncio
from lightrag import LightRAG

from lightrag.llm.openai import openai_complete, openai_embed
from lightrag.utils import EmbeddingFunc, always_get_an_event_loop
from lightrag import QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from api_config import MODEL_CONFIG, CHAT_MODEL, EMBEDDING_MODEL

# WorkingDir
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(ROOT_DIR, "./test_book")
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)
print(f"WorkingDir: {WORKING_DIR}")

api_key = "empty"


async def initialize_rag():
    # 获取模型配置
    chat_model_config = MODEL_CONFIG[CHAT_MODEL]
    embedding_model_config = MODEL_CONFIG[EMBEDDING_MODEL]

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=openai_complete,
        llm_model_name=CHAT_MODEL,
        llm_model_max_async=4,
        llm_model_max_token_size=chat_model_config["max_token_size"],
        llm_model_kwargs={
            "base_url": chat_model_config["base_url"],
            "api_key": chat_model_config["api_key"],
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=embedding_model_config["embedding_dim"],
            max_token_size=embedding_model_config["max_token_size"],
            func=lambda texts: openai_embed(
                texts=texts,
                model=EMBEDDING_MODEL,
                base_url=embedding_model_config["base_url"],
                api_key=embedding_model_config["api_key"],
            ),
        ),
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag


async def print_stream(stream):
    async for chunk in stream:
        if chunk:
            print(chunk, end="", flush=True)


def main():
    # Initialize RAG instance
    rag = asyncio.run(initialize_rag())

    with open("./book.txt", "r", encoding="utf-8") as f:
        rag.insert(f.read())

    while True:
        question = input("请输入问题：")
        resp = rag.query(
            question,
            param=QueryParam(mode="hybrid", stream=True),
        )

        loop = always_get_an_event_loop()
        if inspect.isasyncgen(resp):
            loop.run_until_complete(print_stream(resp))
        else:
            print(resp)
        print("\n--------------------------------")


if __name__ == "__main__":
    main()
