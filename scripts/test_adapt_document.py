#!/usr/bin/env python3
"""
Test script for the document adaptation workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.adapt_document import main

async def test_document_adaptation():
    """Test the document adaptation workflow."""
    print("=== Document Adaptation Test ===")
    
    # Path to the test document
    doc_path = PROJECT_ROOT / "workspace" / "simple_test_document.md"
    
    # Check if the test document exists
    if not doc_path.exists():
        print(f"Error: Test document not found at {doc_path}")
        return
    
    # Test adaptation prompt - simpler and more specific
    prompt = "Change 'This is a simple test document.' to 'This is a formal test document.' Also change 'This is the introduction section.' to 'This section provides an overview of the document.'"
    
    print(f"Test document: {doc_path}")
    print(f"Adaptation prompt: {prompt}")
    print()
    
    # Run the adaptation
    try:
        await main(str(doc_path), prompt)
        print()
        print("=== Test Completed ===")
        
        # Show the modified document
        print("Modified document content:")
        print("-" * 40)
        modified_content = doc_path.read_text(encoding='utf-8')
        print(modified_content)
        print("-" * 40)
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_adaptation())