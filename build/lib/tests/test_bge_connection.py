# tests/test_bge_connection.py
import os
import sys
from pathlib import Path
from unittest.mock import patch

# --- 【核心修正】添加路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# --------------------------------

import pytest
from llama_index.embeddings.openai import OpenAIEmbedding
from metagpt.config2 import Config
from metagpt.rag.factories.embedding import RAGEmbeddingFactory

# 模拟的config2.yaml内容
MOCK_CONFIG_YAML = """
embedding:
  api_type: "openai"
  model: "bge-large-zh-v1.5"
  base_url: "http://127.0.0.1:8888/v1"
  api_key: "sk-dummy-for-test"
  embed_batch_size: 16
"""

@pytest.fixture
def mock_config(tmp_path):
    """创建一个临时的、内容被模拟的配置文件。"""
    config_path = tmp_path / "config2.yaml"
    config_path.write_text(MOCK_CONFIG_YAML)
    return str(config_path)

def test_bge_factory_creation(mock_config):
    """AC1.1: 测试BGE服务连接配置和工厂创建。"""
    # 使用patch确保Config从我们的模拟文件加载
    with patch.object(Config, 'DEFAULT_PATH', new=Path(mock_config)):
        config = Config.from_yaml_file(mock_config)
        
        # 1. 创建嵌入模型实例
        embedding_instance = RAGEmbeddingFactory.create(config=config)

        # 2. 断言返回的对象类型正确
        assert isinstance(embedding_instance, OpenAIEmbedding), \
            "Factory should return an OpenAIEmbedding instance for 'openai' api_type."

        # 3. 断言api_base属性正确指向BGE服务地址
        expected_base_url = "http://127.0.0.1:8888/v1"
        assert embedding_instance.api_base == expected_base_url, \
            f"Instance api_base should be '{expected_base_url}'."
        
        assert embedding_instance.model_name == "bge-large-zh-v1.5"
        assert embedding_instance.embed_batch_size == 16


@pytest.mark.skipif(not os.getenv("RUN_BGE_SERVICE_TEST"), reason="BGE服务未运行时跳过此测试")
def test_bge_service_embedding(mock_config):
    """
    (可选) 实际调用嵌入服务进行测试。
    运行前请确保BGE服务在 http://127.0.0.1:8888 运行。
    并通过 `export RUN_BGE_SERVICE_TEST=1` 激活测试。
    """
    with patch.object(Config, 'DEFAULT_PATH', new=Path(mock_config)):
        config = Config.from_yaml_file(mock_config)
        embedding_instance = RAGEmbeddingFactory.create(config=config)

        # 调用 get_text_embedding
        test_text = "测试"
        embedding_vector = embedding_instance.get_text_embedding(test_text)

        # 断言返回的是一个向量（列表）且长度正确（bge-large-zh-v1.5是1024维）
        assert isinstance(embedding_vector, list)
        assert len(embedding_vector) == 1024, "The embedding dimension for bge-large-zh-v1.5 should be 1024."