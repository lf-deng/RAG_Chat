import asyncio
import inspect
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import openai_complete, openai_embed
from lightrag.utils import EmbeddingFunc, always_get_an_event_loop
from api_config import MODEL_CONFIG, CHAT_MODEL, EMBEDDING_MODEL
import os

# WorkingDir
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 全局变量
rag = None
current_kb = None


async def initialize_rag(kb_name):
    """初始化RAG，需要指定知识库名称"""
    global rag, current_kb

    # 设置工作目录
    working_dir = os.path.join(ROOT_DIR, f"./local_kb/{kb_name}")
    if not os.path.exists(working_dir):
        raise ValueError(f"知识库 '{kb_name}' 不存在！")

    # 获取模型配置
    chat_model_config = MODEL_CONFIG[CHAT_MODEL]
    embedding_model_config = MODEL_CONFIG[EMBEDDING_MODEL]

    rag = LightRAG(
        working_dir=working_dir,
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


def load_knowledge_base(kb_name):
    """加载指定的知识库"""
    global rag, current_kb
    try:
        loop = always_get_an_event_loop()
        # 初始化 RAG
        rag = loop.run_until_complete(initialize_rag(kb_name))
        current_kb = kb_name
        return True
    except Exception as e:
        print(f"加载知识库时发生错误: {e}")
        return False


def ensure_rag():
    """确保RAG已经初始化"""
    global rag, current_kb
    if rag is None:
        raise ValueError("请先选择并加载知识库！")
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
        # 检查是否已选择知识库
        if current_kb is None:
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "请先选择一个知识库！"},
            ]
            yield history
            return

        rag_instance = ensure_rag()

        print("开始构建历史消息")
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
        print("完成历史消息构建")

        # 获取回复流
        print("开始查询")
        resp = rag_instance.query(
            message,
            param=QueryParam(
                mode="hybrid", stream=True, conversation_history=history_messages
            ),
        )

        loop = always_get_an_event_loop()
        if inspect.isasyncgen(resp):
            # 初始化用户消息和助手消息
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": ""},
            ]

            async def stream_response():
                response_text = ""
                async for chunk in resp:
                    if chunk:
                        response_text += chunk
                        # 更新助手的回复
                        history[-1]["content"] = response_text
                        yield history

            # 处理流式响应
            async_gen = stream_response()
            while True:
                try:
                    history_update = loop.run_until_complete(async_gen.__anext__())
                    yield history_update
                except StopAsyncIteration:
                    break
        else:
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": resp},
            ]
            yield history
    except Exception as e:
        print(f"聊天过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"抱歉，处理您的请求时发生错误: {str(e)}"},
        ]
        yield history
