import asyncio
import inspect
import os
import traceback
from typing import List, Dict, Any, Optional, Union, AsyncGenerator

from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import openai_complete, openai_embed
from lightrag.utils import EmbeddingFunc, always_get_an_event_loop
from api_config import MODEL_CONFIG, CHAT_MODEL, EMBEDDING_MODEL

# 工作目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 全局变量
rag = None
current_kb = None
welcome_message = "请先选择一个知识库！"


def set_welcome_message(message: str):
    """设置欢迎消息

    Args:
        message: 欢迎消息内容
    """
    global welcome_message
    welcome_message = message


def reset_welcome_state():
    """重置欢迎消息状态，用于清除聊天记录后"""
    # 这个函数保留用于接口兼容，实际上不需要做任何事情
    pass


def get_welcome_message():
    """获取欢迎消息

    Returns:
        str: 欢迎消息
    """
    global welcome_message
    return welcome_message


async def initialize_rag(kb_name: str) -> LightRAG:
    """初始化RAG，需要指定知识库名称

    Args:
        kb_name: 知识库名称

    Returns:
        LightRAG: 初始化好的RAG实例

    Raises:
        ValueError: 知识库不存在时抛出
        Exception: 初始化过程中的其他错误
    """
    global rag, current_kb

    # 设置工作目录
    working_dir = os.path.join(ROOT_DIR, f"./local_kb/{kb_name}")
    if not os.path.exists(working_dir):
        raise ValueError(f"知识库 '{kb_name}' 不存在！")

    # 获取模型配置
    chat_model_config = MODEL_CONFIG.get(CHAT_MODEL, {})
    embedding_model_config = MODEL_CONFIG.get(EMBEDDING_MODEL, {})

    if not chat_model_config or not embedding_model_config:
        raise ValueError(
            f"模型配置错误: 找不到 {CHAT_MODEL} 或 {EMBEDDING_MODEL} 的配置"
        )

    try:
        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=openai_complete,
            llm_model_name=CHAT_MODEL,
            llm_model_max_async=4,
            llm_model_max_token_size=chat_model_config.get("max_token_size", 4096),
            llm_model_kwargs={
                "base_url": chat_model_config.get("base_url", ""),
                "api_key": chat_model_config.get("api_key", ""),
            },
            embedding_func=EmbeddingFunc(
                embedding_dim=embedding_model_config.get("embedding_dim", 1536),
                max_token_size=embedding_model_config.get("max_token_size", 8191),
                func=lambda texts: openai_embed(
                    texts=texts,
                    model=EMBEDDING_MODEL,
                    base_url=embedding_model_config.get("base_url", ""),
                    api_key=embedding_model_config.get("api_key", ""),
                ),
            ),
        )

        await rag.initialize_storages()
        await initialize_pipeline_status()

        current_kb = kb_name
        print(f"成功初始化知识库: {kb_name}")
        return rag
    except Exception as e:
        print(f"初始化RAG时发生错误: {e}")
        traceback.print_exc()
        raise


def load_knowledge_base_rag(kb_name: str) -> bool:
    """加载指定的知识库

    Args:
        kb_name: 知识库名称

    Returns:
        bool: 是否成功加载知识库
    """
    global rag, current_kb
    try:
        if not kb_name or kb_name == "请选择一个知识库":
            print("未选择有效的知识库")
            return False

        loop = always_get_an_event_loop()
        # 初始化 RAG
        rag = loop.run_until_complete(initialize_rag(kb_name))
        current_kb = kb_name
        return True
    except Exception as e:
        print(f"加载知识库时发生错误: {e}")
        traceback.print_exc()
        return False


def ensure_rag() -> LightRAG:
    """确保RAG已经初始化

    Returns:
        LightRAG: 当前RAG实例

    Raises:
        ValueError: 如果RAG未初始化
    """
    global rag, current_kb
    if rag is None:
        raise ValueError("请先选择并加载知识库！")
    return rag


def chat_with_rag(message: str, history: List[Dict[str, str]]) -> AsyncGenerator:
    """与RAG进行对话

    Args:
        message: 用户消息
        history: 对话历史

    Yields:
        更新后的对话历史
    """
    try:
        # 检查是否已选择知识库
        if current_kb is None and message:
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "请先选择一个知识库！"},
            ]
            yield history
            return

        # 如果没有用户消息，直接返回当前历史
        if not message:
            yield history
            return

        rag_instance = ensure_rag()

        # 构建历史消息
        print("开始构建历史消息")
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
        print(f"开始查询: {message[:50]}...")
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
                try:
                    async for chunk in resp:
                        if chunk:
                            response_text += chunk
                            # 更新助手的回复
                            history[-1]["content"] = response_text
                            yield history
                except Exception as e:
                    print(f"流式响应处理错误: {e}")
                    traceback.print_exc()
                    history[-1][
                        "content"
                    ] = f"{response_text}\n[处理响应时发生错误: {str(e)}]"
                    yield history

            # 处理流式响应
            async_gen = stream_response()
            while True:
                try:
                    history_update = loop.run_until_complete(async_gen.__anext__())
                    yield history_update
                except StopAsyncIteration:
                    break
                except Exception as e:
                    print(f"处理流式响应迭代时发生错误: {e}")
                    traceback.print_exc()
                    history[-1][
                        "content"
                    ] = f"{history[-1]['content']}\n[处理响应时发生错误: {str(e)}]"
                    yield history
                    break
        else:
            # 非流式响应
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": resp},
            ]
            yield history
    except Exception as e:
        print(f"聊天过程中发生错误: {e}")
        traceback.print_exc()
        # 确保即使发生错误，也能返回一个有效的响应
        if (
            not history
            or not isinstance(history[-1], dict)
            or history[-1].get("role") != "assistant"
        ):
            history = history + [
                {"role": "user", "content": message},
                {
                    "role": "assistant",
                    "content": f"抱歉，处理您的请求时发生错误: {str(e)}",
                },
            ]
        else:
            # 如果最后一条已经是assistant的消息，则更新它
            history[-1]["content"] = f"抱歉，处理您的请求时发生错误: {str(e)}"
        yield history
