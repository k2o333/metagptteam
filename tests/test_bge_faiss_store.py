# tests/test_bge_faiss_store.py
import sys
from pathlib import Path
import numpy as np
import pytest

# 路径设置，现在应该可以正常工作了
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.rag.stores.bge_faiss_store import BGEFAISSStore

DIMENSION = 8

@pytest.fixture
def mock_vectors():
    return { "minhash1": list(np.random.random(DIMENSION)) }

def test_add_and_persist(tmp_path, mock_vectors):
    store = BGEFAISSStore(persist_path=str(tmp_path))
    for sig, vec in mock_vectors.items():
        store.add_vector(sig, vec)
    store.persist()
    assert (tmp_path / "bge.faiss").exists()

def test_load(tmp_path, mock_vectors):
    store1 = BGEFAISSStore(persist_path=str(tmp_path))
    store1.add_vector("minhash1", mock_vectors["minhash1"])
    store1.persist()
    
    store2 = BGEFAISSStore(persist_path=str(tmp_path))
    assert store2.faiss_index.ntotal == 1

def test_search(tmp_path, mock_vectors):
    store = BGEFAISSStore(persist_path=str(tmp_path))
    store.add_vector("minhash1", mock_vectors["minhash1"])
    retrieved_vec = store.search("minhash1")
    assert retrieved_vec is not None
    np.testing.assert_allclose(retrieved_vec, np.array(mock_vectors["minhash1"]), atol=1e-6)