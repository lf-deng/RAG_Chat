import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
import numpy as np
from lightrag.kg.shared_storage import initialize_pipeline_status

from api_config import MODEL_CONFIG, CHAT_MODEL, EMBEDDING_MODEL, ModelType

WORKING_DIR = "./test_book"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    # 获取聊天模型配置
    model_config = MODEL_CONFIG[CHAT_MODEL]

    return await openai_complete_if_cache(
        CHAT_MODEL,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=model_config["api_key"],
        base_url=model_config["base_url"],
        **kwargs,
    )


async def embedding_func(texts: list[str]) -> np.ndarray:
    # 获取嵌入模型配置
    model_config = MODEL_CONFIG[EMBEDDING_MODEL]

    return await openai_embed(
        texts,
        model=EMBEDDING_MODEL,
        api_key=model_config["api_key"],
        base_url=model_config["base_url"],
    )


async def get_embedding_dim():
    # 直接从配置中获取嵌入维度
    return MODEL_CONFIG[EMBEDDING_MODEL]["embedding_dim"]


# function test
async def test_funcs():
    result = await llm_model_func("你是谁?模型名称？")
    print("llm_model_func: ", result)

    result = await embedding_func(["How are you?"])
    print("embedding_func: ", result)


async def initialize_rag():
    embedding_dimension = await get_embedding_dim()
    print(f"Detected embedding dimension: {embedding_dimension}")

    # 获取嵌入模型配置
    model_config = MODEL_CONFIG[EMBEDDING_MODEL]

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=embedding_dimension,
            max_token_size=model_config["max_token_size"],
            func=embedding_func,
        ),
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag


async def main():
    try:
        print("初始化RAG实例...")
        # Initialize RAG instance
        rag = await initialize_rag()
        print("初始化完成...")

        with open("./book.txt", "r", encoding="utf-8") as f:
            print("插入数据...")
            await rag.ainsert(f.read())

        while True:
            question = input("请输入问题：")
            print(
                await rag.aquery(
                    question,
                    param=QueryParam(mode="hybrid"),
                )
            )
            print("--------------------------------")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("开始...")
    asyncio.run(main())
