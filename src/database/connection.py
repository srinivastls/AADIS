
import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
from config.settings import settings
from models.document_models import Base
from typing import Dict, Any

class DatabaseManager:
    def __init__(self):
        # SQLite setup
        self.engine = create_engine(settings.SQLITE_URL, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        # Chroma setup
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.chroma_client.get_or_create_collection(
            name="document_embeddings",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Embedding model
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    def get_db_session(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def add_text_embedding(self, text: str, metadata: Dict[str, Any]) -> str:
        """Add text embedding to Chroma"""
        embedding = self.embedding_model.encode([text])
        
        # Generate unique ID
        import uuid
        vector_id = str(uuid.uuid4())
        
        self.collection.add(
            embeddings=embedding.tolist(),
            documents=[text],
            metadatas=[metadata],
            ids=[vector_id]
        )
        
        return vector_id

# Global database manager instance
db_manager = DatabaseManager()