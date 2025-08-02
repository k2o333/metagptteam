# scripts/ingest_docs.py (修复版)

import argparse
import asyncio
import sys
from pathlib import Path

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# -----------------

from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.node_parser import TokenTextSplitter
from metagpt.logs import logger

from hierarchical.rag.engines.docrag_engine import DocRAGEngine

# 为llama-index设置一个安静的日志级别，避免过多输出
import logging
logging.getLogger("llama_index.core.readers.file.base").setLevel(logging.WARNING)

async def main(source_dir: str, persist_path: str, chunk_size: int, chunk_overlap: int):
    """
    主函数，执行文档的加载、切分和摄入。
    """
    source_path = Path(source_dir)
    persist_path_obj = Path(persist_path)

    if not source_path.is_dir():
        logger.error(f"Source directory not found: {source_path}")
        return

    logger.info("--- Starting Document Ingestion ---")
    logger.info(f"Source Directory: {source_path}")
    logger.info(f"RAG Persist Path: {persist_path_obj}")
    logger.info(f"Chunk Size: {chunk_size}, Chunk Overlap: {chunk_overlap}")

    # 1. 【核心修复】使用异步工厂方法 from_path() 来实例化 DocRAGEngine
    docrag_engine = await DocRAGEngine.from_path(persist_path=str(persist_path_obj))

    # 2. 加载文档 (只加载MD和TXT文件)
    logger.info("Loading documents from source directory...")
    reader = SimpleDirectoryReader(
        input_dir=str(source_path),
        required_exts=[".md", ".txt"],
        recursive=True
    )
    documents = reader.load_data()
    if not documents:
        logger.warning("No documents (.md, .txt) found in the source directory.")
        return
    logger.success(f"Loaded {len(documents)} documents.")

    # 3. 初始化文本切分器
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # 4. 切分文档并提取文本和元数据
    logger.info("Splitting documents into text chunks (nodes)...")
    nodes = splitter.get_nodes_from_documents(documents)
    logger.success(f"Split documents into {len(nodes)} chunks.")

    if not nodes:
        logger.warning("No text chunks were generated after splitting. Nothing to ingest.")
        return

    all_texts = [node.get_content() for node in nodes]
    all_metadatas = [node.metadata.copy() for node in nodes]
    
    # 为每个块添加一个唯一的块ID作为元数据
    for i, meta in enumerate(all_metadatas):
        meta["chunk_id"] = i

    # 5. 调用 DocRAGEngine 的 add_texts 方法进行摄入
    logger.info(f"Ingesting {len(all_texts)} text chunks into the RAG engine...")
    await docrag_engine.add_texts(texts=all_texts, metadatas=all_metadatas)
    
    logger.success("--- Document Ingestion Complete! ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into the DocRAGEngine.")
    parser.add_argument(
        "--source_dir", 
        type=str, 
        required=True, 
        help="Directory containing the source documents (e.g., .md, .txt)."
    )
    parser.add_argument(
        "--persist_path", 
        type=str, 
        required=True, 
        help="The path where the RAG engine's data should be persisted."
    )
    parser.add_argument(
        "--chunk_size", 
        type=int, 
        default=1024, 
        help="The token chunk size for splitting documents."
    )
    parser.add_argument(
        "--chunk_overlap", 
        type=int, 
        default=100, 
        help="The token overlap between chunks."
    )

    args = parser.parse_args()

    # 创建一个示例目录和文件以便快速测试
    sample_data_dir = Path("sample_docs")
    if args.source_dir == str(sample_data_dir):
        sample_data_dir.mkdir(exist_ok=True)
        (sample_data_dir / "doc1.md").write_text("# Hello World\nThis is a test document.")
        (sample_data_dir / "doc2.txt").write_text("Another test document about AI and RAG.")

    asyncio.run(main(
        source_dir=args.source_dir,
        persist_path=args.persist_path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    ))
    
    print(f"\nTo run this script:\npython scripts/ingest_docs.py --source_dir sample_docs --persist_path my_rag_db")