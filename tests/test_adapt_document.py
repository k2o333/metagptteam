#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本，用于验证adapt_document.py的修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_document_exists():
    """测试文档文件是否存在"""
    doc_path = PROJECT_ROOT / "test_docs" / "sample_document.md"
    assert doc_path.exists(), f"文档文件不存在: {doc_path}"
    print("✓ 文档文件存在")

def test_config_files():
    """测试配置文件是否存在"""
    global_config_path = Path("/root/.metagpt/config2.yaml")
    local_config_path = PROJECT_ROOT / "configs" / "local_config.yaml"
    
    assert global_config_path.exists(), f"全局配置文件不存在: {global_config_path}"
    assert local_config_path.exists(), f"本地配置文件不存在: {local_config_path}"
    print("✓ 配置文件存在")

async def test_adapt_document():
    """测试adapt_document脚本"""
    doc_path = PROJECT_ROOT / "test_docs" / "sample_document.md"
    
    # 导入并运行主函数
    from scripts.adapt_document import main
    
    try:
        await main(str(doc_path), "Subsection B写得太简单了，丰富一下")
        print("✓ adapt_document脚本运行成功")
        return True
    except Exception as e:
        print(f"✗ adapt_document脚本运行失败: {e}")
        return False

def test_output_file():
    """测试输出文件是否生成"""
    workspace_dir = PROJECT_ROOT / "workspace"
    if workspace_dir.exists():
        # 查找最新生成的文件
        files = list(workspace_dir.glob("sample_document_*.md"))
        if files:
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            content = latest_file.read_text()
            if "这是B部分的内容，需要丰富。" in content and len(content) > 200:
                print("✓ 输出文件生成正确，内容已丰富")
                return True
            else:
                print("✗ 输出文件内容不正确")
                return False
        else:
            print("✗ 未找到输出文件")
            return False
    else:
        print("✗ workspace目录不存在")
        return False

async def main():
    """主测试函数"""
    print("开始测试adapt_document修复...")
    
    try:
        # 运行各项测试
        test_document_exists()
        test_config_files()
        
        success = await test_adapt_document()
        if not success:
            return False
            
        success = test_output_file()
        if not success:
            return False
            
        print("\n所有测试通过！")
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)