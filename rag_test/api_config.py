# api_config.py
# 集中管理API配置的模块，提供统一的接口获取不同模型的配置信息

import os
import typing
from enum import Enum


class ModelType(str, Enum):
    """模型类型枚举"""

    CHAT = "chat"
    EMBEDDING = "embedding"


class ModelProvider(str, Enum):
    """模型提供商枚举"""

    ZHIPU = "ZHIPU"
    DEEPSEEK = "DEEPSEEK"


# API密钥配置
ZHIPU_API_KEY = "9f91888979124986a65c08e690f3b5a9.7a4PIjBXc7q4lIzE"
DEEPSEEK_API_KEY = "sk-1551464ac89447c59470fb92bbc230b3"

# 默认使用的模型
CHAT_MODEL = "glm-4-flash"
EMBEDDING_MODEL = "embedding-2"

# 模型配置字典，按模型名称索引
MODEL_CONFIG: dict[str, dict[str, typing.Any]] = {
    # 智谱AI模型
    "glm-4-flash": {
        "provider": ModelProvider.ZHIPU,
        "type": ModelType.CHAT,
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key": ZHIPU_API_KEY,
        "max_token_size": 8192,
    },
    "embedding-2": {
        "provider": ModelProvider.ZHIPU,
        "type": ModelType.EMBEDDING,
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key": ZHIPU_API_KEY,
        "embedding_dim": 1024,
        "max_token_size": 8192,
    },
    "embedding-3": {
        "provider": ModelProvider.ZHIPU,
        "type": ModelType.EMBEDDING,
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key": ZHIPU_API_KEY,
        "embedding_dim": 1024,
        "max_token_size": 8192,
    },
    # DeepSeek模型
    "deepseek-chat": {
        "provider": ModelProvider.DEEPSEEK,
        "type": ModelType.CHAT,
        "base_url": "https://api.deepseek.com",
        "api_key": DEEPSEEK_API_KEY,
        "max_token_size": 8192,
    },
}
