
import os
from pathlib import Path

def create_project_structure():
    """Create the project directory structure"""
    
    dirs = [
        "src",
        "src/agents/qa_agents",
        "src/database", 
        "src/models",
        "src/utils",
        "src/interfaces",
        "config",
        "data",
        "data/input",
        "data/processed",
        "data/images",
        "logs",
        "tests"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
    print("Project structure created successfully!")

if __name__ == "__main__":
    create_project_structure()