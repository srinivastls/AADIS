
import os
from pathlib import Path
from typing import List, Dict, Any
import magic
import mimetypes

def get_supported_file_types() -> List[str]:
    """Get list of supported file extensions"""
    return ['.pdf', '.docx', '.doc']

def validate_file_type(file_path: str) -> bool:
    """Validate if file type is supported"""
    return Path(file_path).suffix.lower() in get_supported_file_types()

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get detailed file information"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = path.stat()
    
    return {
        "filename": path.name,
        "filepath": str(path.absolute()),
        "file_size": stat.st_size,
        "file_type": path.suffix.lower(),
        "created_time": stat.st_ctime,
        "modified_time": stat.st_mtime,
        "is_supported": validate_file_type(file_path)
    }

def scan_directory(directory_path: str) -> List[Dict[str, Any]]:
    """Scan directory for supported documents"""
    directory = Path(directory_path)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    supported_files = []
    supported_extensions = get_supported_file_types()
    
    for ext in supported_extensions:
        for file_path in directory.glob(f"*{ext}"):
            try:
                file_info = get_file_info(str(file_path))
                supported_files.append(file_info)
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
    
    return supported_files