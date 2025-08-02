# tests/test_hashing.py (新建)
import sys
from pathlib import Path
import pytest

# 确保能找到 hierarchical 模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.rag.utils.hashing import (
    generate_minhash_signature,
    semantic_fingerprint,
)

def test_generate_minhash_is_deterministic():
    """AC2.1: 确保MinHash对于相同输入有相同输出。"""
    text1 = "The quick brown fox jumps over the lazy dog"
    text2 = "The quick brown fox jumps over the lazy dog"
    
    hash1 = generate_minhash_signature(text1)
    hash2 = generate_minhash_signature(text2)
    
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) > 0

def test_generate_minhash_is_sensitive():
    """AC2.1: 确保MinHash对于不同输入有不同输出。"""
    text1 = "The quick brown fox jumps over the lazy dog"
    text3 = "The quick brown fox jumps over the happy dog"
    
    hash1 = generate_minhash_signature(text1)
    hash3 = generate_minhash_signature(text3)
    
    assert hash1 != hash3

def test_semantic_fingerprint_is_deterministic():
    """AC2.1: 确保语义指纹对于相同输入有相同输出。"""
    vector1 = [0.1, -0.5, 1.2, -0.9]
    vector2 = [0.1, -0.5, 1.2, -0.9]
    
    fp1 = semantic_fingerprint(vector1)
    fp2 = semantic_fingerprint(vector2)
    
    assert fp1 == fp2
    assert fp1 == "1010"

def test_semantic_fingerprint_is_sensitive():
    """AC2.1: 确保语义指纹对于不同输入有不同输出。"""
    vector1 = [0.1, -0.5, 1.2, -0.9]
    vector3 = [-0.1, 0.5, -1.2, 0.9]
    
    fp1 = semantic_fingerprint(vector1)
    fp3 = semantic_fingerprint(vector3)
    
    assert fp1 != fp3
    assert fp3 == "0101"