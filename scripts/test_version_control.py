import sys
from pathlib import Path

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.utils_pkg.version_control import VersionControl

def main():
    # Test the version control functionality
    test_file = Path("test_docs/sample_document.md")
    if test_file.exists():
        print(f"Original file: {test_file}")
        versioned_file = VersionControl.create_versioned_copy(test_file)
        print(f"Versioned copy created: {versioned_file}")
    else:
        print(f"Test file not found: {test_file}")

if __name__ == "__main__":
    main()