import os
import re
from pathlib import Path
from datetime import datetime
from typing import Union


class VersionControl:
    """
    A utility class for creating timestamped versions of files.
    """
    
    @staticmethod
    def create_versioned_copy(file_path: Union[str, Path]) -> Path:
        """
        Creates a timestamped copy of a file.
        
        Args:
            file_path: Path to the original file
            
        Returns:
            Path to the newly created versioned copy
            
        Raises:
            FileNotFoundError: If the original file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Original file not found: {file_path}")
            
        # Get the parent directory, stem (filename without extension), and extension
        parent_dir = file_path.parent
        stem = file_path.stem
        suffix = file_path.suffix
        
        # Remove existing timestamp from stem if present
        # Pattern matches _YYYYMMDDHHMMSS at the end of the stem
        timestamp_pattern = r'_\d{14}$'
        clean_stem = re.sub(timestamp_pattern, '', stem)
        
        # Generate a unique timestamped filename
        while True:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{clean_stem}_{timestamp}{suffix}"
            new_file_path = parent_dir / new_filename
            
            # Check if file already exists
            if not new_file_path.exists():
                break
                
            # If it exists, wait a second and try again
            datetime.now().replace(microsecond=0).second += 1
        
        # Copy the original file to the new versioned file
        with open(file_path, 'r', encoding='utf-8') as original_file:
            with open(new_file_path, 'w', encoding='utf-8') as new_file:
                new_file.write(original_file.read())
                
        return new_file_path