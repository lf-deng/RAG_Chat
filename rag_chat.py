import asyncio
import inspect
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete, openai_embed
from lightrag.utils import EmbeddingFunc, always_get_an_event_loop
from api_config import MODEL_CONFIG, CHAT_MODEL, EMBEDDING_MODEL
import os

# WorkingDir
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(ROOT_DIR, "./local_kb/test_book")
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# 全局RAG实例
rag = None


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

    # 初始化存储，这会自动加载已存在的数据
    await rag.initialize_storages()
    return rag


def ensure_rag():
    global rag
    if rag is None:
        loop = always_get_an_event_loop()
        rag = loop.run_until_complete(initialize_rag())
    return rag


async def process_stream(stream, message, history):
    try:
        response = ""
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": ""},
        ]
        async for chunk in stream:
            if chunk:
                response += chunk
                history[-1]["content"] = response
                yield history
    except Exception as e:
        print(f"处理流时发生错误: {e}")
        raise


def chat_with_rag(message, history):
    try:
        rag_instance = ensure_rag()

        # 构建历史消息
        history_messages = []
        for msg in history:
            if isinstance(msg, dict):
                # 如果已经是字典格式
                history_messages.append(msg)
            else:
                # 如果是旧的元组格式，转换为字典格式
                role = "user" if len(history_messages) % 2 == 0 else "assistant"
                history_messages.append({"role": role, "content": msg})

        # 获取回复流
        resp = rag_instance.query(
            message,
            param=QueryParam(
                mode="hybrid", stream=True, conversation_history=history_messages
            ),
        )

        loop = always_get_an_event_loop()
        if inspect.isasyncgen(resp):
            for history_update in loop.run_until_complete(
                process_stream(resp, message, history)
            ):
                yield history_update
        else:
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": resp},
            ]
            yield history
    except Exception as e:
        print(f"聊天过程中发生错误: {e}")
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"抱歉，处理您的请求时发生错误: {str(e)}"},
        ]
        yield history
