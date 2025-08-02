# hierarchical/rag/utils/hashing.py (新建)
import base64
from typing import List

import numpy as np
from datasketch import MinHash

def generate_minhash_signature(text: str, num_perm: int = 128) -> str:
    """
    从文本生成MinHash签名。
    此方法对句法相似性敏感。相同的文本将始终产生相同的签名。

    :param text: 输入的文本字符串。
    :param num_perm: MinHash中使用的排列函数数量，影响签名的精度和大小。
    :return: Base64编码的MinHash签名字符串。
    """
    if not text:
        return ""
        
    m = MinHash(num_perm=num_perm)
    # 使用单词作为分片 (shingles)
    for word in text.split():
        m.update(word.encode('utf8'))
        
    # 序列化hashvalues并用base64编码，以获得一个可存储的字符串
    return base64.b64encode(m.hashvalues.tobytes()).decode('utf-8')

def semantic_fingerprint(embedding_vector: List[float]) -> str:
    """
    从嵌入向量生成一个简单的二进制语义指纹。
    此方法基于向量中每个分量的正负号，是一种简化的局部敏感哈希（LSH）。
    语义相似的向量（方向大致相同）将产生相似（汉明距离近）的指纹。

    :param embedding_vector: 输入的浮点数嵌入向量。
    :return: '0'和'1'组成的二进制字符串指纹。
    """
    if not embedding_vector:
        return ""
        
    # 将向量转换为numpy数组以便进行矢量化操作
    np_vector = np.array(embedding_vector)
    
    # 如果分量 > 0 则为1，否则为0
    binary_vector = (np_vector > 0).astype(int)
    
    # 将二进制数组转换为字符串，例如 [1, 0, 1] -> "101"
    return "".join(map(str, binary_vector))