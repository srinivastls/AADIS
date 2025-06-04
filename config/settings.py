
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Database Configuration
    SQLITE_URL: str = "sqlite:///./data/documents.db"
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    
    # Processing Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_WORKERS: int = 4
    
    # Model Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Paths
    INPUT_DIR: Path = Path("./data/input")
    PROCESSED_DIR: Path = Path("./data/processed") 
    IMAGES_DIR: Path = Path("./data/images")
    LOGS_DIR: Path = Path("./logs")
    
    # Docling Configuration
    DOCLING_PIPELINE: str = "fast"  # fast, accurate, or custom
    
    class Config:
        env_file = ".env"

settings = Settings()