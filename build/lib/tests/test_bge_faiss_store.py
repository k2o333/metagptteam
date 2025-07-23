# tests/test_bge_faiss_store.py
import sys
from pathlib import Path
import numpy as np
import pytest

# --- 【核心修正】添加路径设置，确保 pytest 能找到 'hierarchical' 模块 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# --------------------------------------------------------------------

from hierarchical.rag.stores.bge_faiss_store import BGEFAISSStore

DIMENSION = 8  # 使用一个小的维度进行测试

@pytest.fixture
def mock_vectors():
    """提供一些模拟的向量和签名。"""
    return {
        "minhash1": list(np.random.random(DIMENSION)),
        "minhash2": list(np.random.random(DIMENSION)),
        "minhash3": list(np.random.random(DIMENSION)),
    }

def test_add_vector_and_persist(tmp_path, mock_vectors):
    """AC1.2: 测试 add_vector 和 persist 方法。"""
    store = BGEFAISSStore(persist_path=str(tmp_path))

    # 1. 添加向量
    for sig, vec in mock_vectors.items():
        store.add_vector(sig, vec)
    
    assert store.faiss_index.ntotal == 3
    assert len(store.minhash_to_id) == 3

    # 2. 持久化
    store.persist()

    # 3. 断言文件已创建
    assert (tmp_path / "bge.faiss").exists()
    assert (tmp_path / "minhash_to_id.pkl").exists()

def test_load_from_disk(tmp_path, mock_vectors):
    """AC1.2: 测试新实例能从磁盘恢复状态。"""
    # 准备环境：先创建一个持久化的store
    store1 = BGEFAISSStore(persist_path=str(tmp_path))
    for sig, vec in mock_vectors.items():
        store1.add_vector(sig, vec)
    store1.persist()

    # 创建一个新实例，它应该会自动加载数据
    store2 = BGEFAISSStore(persist_path=str(tmp_path))

    # 断言状态已恢复
    assert store2.faiss_index is not None
    assert store2.faiss_index.ntotal == 3
    assert len(store2.minhash_to_id) == 3
    assert "minhash2" in store2.minhash_to_id

def test_search_and_similarity_search(tmp_path, mock_vectors):
    """AC1.2: 测试 search 和 similarity_search 方法。"""
    store = BGEFAISSStore(persist_path=str(tmp_path))
    for sig, vec in mock_vectors.items():
        store.add_vector(sig, vec)

    # 1. 测试 search (通过MinHash精确查找)
    target_sig = "minhash1"
    expected_vec = np.array(mock_vectors[target_sig])
    retrieved_vec = store.search(target_sig)

    assert retrieved_vec is not None
    np.testing.assert_allclose(retrieved_vec, expected_vec, atol=1e-6)
    
    # 测试查找不存在的签名
    assert store.search("non_existent_minhash") is None

    # 2. 测试 similarity_search (通过向量内容模糊查找)
    query_vec = mock_vectors["minhash2"]
    # 添加一点点噪声
    query_vec_noisy = (np.array(query_vec) + np.random.normal(0, 0.01, DIMENSION)).tolist()

    distances, indices = store.similarity_search(query_vec_noisy, k=1)
    
    assert indices.shape == (1, 1)
    
    # 找到的向量ID应该对应于"minhash2"的ID
    expected_id = store.minhash_to_id["minhash2"]
    assert indices[0][0] == expected_id