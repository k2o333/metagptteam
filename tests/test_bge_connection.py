# tests/test_bge_connection.py (The Definitive Final Version)
import os
from pathlib import Path
import pytest
from metagpt.config2 import Config
from metagpt.rag.factories.embedding import RAGEmbeddingFactory
from llama_index.embeddings.openai import OpenAIEmbedding

MOCK_CONFIG_YAML = """
llm:
  api_type: "openai"
  model: "gpt-4"
  api_key: "sk-dummy"

embedding:
  api_type: "openai"
  model: "bge-large-zh-v1.5"
  base_url: "http://127.0.0.1:8888/v1"
  api_key: "sk-dummy-for-test"
  embed_batch_size: 16
"""

@pytest.fixture
def mock_config_file(tmp_path) -> Path:
    """Creates a temporary mock config file and returns its Path object."""
    config_path = tmp_path / "config2.yaml"
    config_path.write_text(MOCK_CONFIG_YAML)
    return config_path

def test_bge_factory_creation(mock_config_file):
    """AC1.1: Test BGE service connection configuration and factory creation."""
    config = Config.from_yaml_file(mock_config_file)

    # 【核心修正】: 1. Instantiate factory with the full config.
    #              2. Call the correct method: get_rag_embedding()
    factory = RAGEmbeddingFactory(config=config)
    embedding_instance = factory.get_rag_embedding()

    assert isinstance(embedding_instance, OpenAIEmbedding)
    expected_base_url = "http://127.0.0.1:8888/v1"
    assert embedding_instance.api_base == expected_base_url
    assert embedding_instance.model_name == "bge-large-zh-v1.5"
    assert embedding_instance.embed_batch_size == 16

@pytest.mark.skipif(not os.getenv("RUN_BGE_SERVICE_TEST"), reason="BGE service not run")
def test_bge_service_embedding(mock_config_file):
    """(Optional) Test actual embedding call to a running service."""
    config = Config.from_yaml_file(mock_config_file)
    
    factory = RAGEmbeddingFactory(config=config)
    embedding_instance = factory.get_rag_embedding()
    
    embedding_vector = embedding_instance.get_text_embedding("测试")
    assert isinstance(embedding_vector, list) and len(embedding_vector) == 1024