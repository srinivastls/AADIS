#!/usr/bin/env python3
"""Database setup and initialization script"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import db_manager
from models.document_models import Base
from config.settings import settings
import logging

def setup_database():
    """Initialize database with all tables and indexes"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=db_manager.engine)
        
        # Initialize Chroma collection
        collection = db_manager.chroma_client.get_or_create_collection(
            name="document_embeddings",
            metadata={"hnsw:space": "cosine"}
        )
        
        print("✅ Database setup completed successfully!")
        print(f"📁 SQLite database: {settings.SQLITE_URL}")
        print(f"📁 Chroma database: {settings.CHROMA_PERSIST_DIR}")
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()